package cmd

import (
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strings"
	"time"

	"tq/store"

	"github.com/spf13/cobra"
)

var (
	addCmd    string
	addPri    int
	addDepStr string
)

func init() {
	addCommand.Flags().StringVar(&addCmd, "cmd", "", "Shell command to execute (required)")
	addCommand.Flags().IntVar(&addPri, "priority", 0, "Task priority (higher = more important)")
	addCommand.Flags().StringVar(&addDepStr, "depends-on", "", "Comma-separated task IDs")
	rootCmd.AddCommand(addCommand)
}

var addCommand = &cobra.Command{
	Use:   "add <name>",
	Short: "Add a task to the queue",
	Args:  cobra.ExactArgs(1),
	RunE:  runAdd,
}

func runAdd(cmd *cobra.Command, args []string) error {
	s := store.NewMemoryStore()
	defer s.Close()
	return runAddWithStore(s, args[0], addCmd, addPri, addDepStr, jsonOutput, os.Stdout)
}

func runAddWithStore(s store.Store, name, cmdStr string, priority int, depStr string, jsonOut bool, w io.Writer) error {
	if cmdStr == "" {
		return fmt.Errorf("tq: cannot add task %q: --cmd is required", name)
	}

	var deps []string
	if depStr != "" {
		deps = strings.Split(depStr, ",")
		// Validate dependencies exist
		tasks, err := s.List(store.Filter{})
		if err != nil {
			return fmt.Errorf("tq: cannot add task %q: %w", name, err)
		}
		existing := make(map[string]bool, len(tasks))
		for _, t := range tasks {
			existing[t.ID] = true
		}
		for _, d := range deps {
			if !existing[d] {
				return fmt.Errorf("tq: cannot add task %q: dependency %q not found", name, d)
			}
		}
	}

	state := store.StateReady
	if len(deps) > 0 {
		state = store.StatePending
	}
	if deps == nil {
		deps = []string{}
	}

	// Pre-generate ID
	b := make([]byte, 4)
	if _, err := rand.Read(b); err != nil {
		return fmt.Errorf("tq: cannot add task %q: %w", name, err)
	}
	id := hex.EncodeToString(b)

	task := store.Task{
		ID:        id,
		Name:      name,
		Cmd:       cmdStr,
		State:     state,
		Priority:  priority,
		DependsOn: deps,
		CreatedAt: time.Now(),
	}

	if err := s.Add(task); err != nil {
		return fmt.Errorf("tq: cannot add task %q: %w", name, err)
	}

	if jsonOut {
		return json.NewEncoder(w).Encode(struct {
			ID string `json:"id"`
		}{ID: id})
	}
	fmt.Fprintln(w, id)
	return nil
}
