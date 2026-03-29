package cmd

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"strconv"

	"tq/store"

	"github.com/spf13/cobra"
)

func init() {
	rootCmd.AddCommand(priorityCommand)
}

var priorityCommand = &cobra.Command{
	Use:   "priority <task-id> <new-priority>",
	Short: "Change a task's priority",
	Args:  cobra.ExactArgs(2),
	RunE:  runPriority,
}

func runPriority(cmd *cobra.Command, args []string) error {
	s := store.NewMemoryStore()
	defer s.Close()
	return runPriorityWithStore(s, args[0], args[1], jsonOutput, os.Stdout)
}

// PriorityResult is the JSON output for the priority command.
type PriorityResult struct {
	ID          string `json:"id"`
	OldPriority int    `json:"old_priority"`
	NewPriority int    `json:"new_priority"`
}

func runPriorityWithStore(s store.Store, id string, priorityStr string, jsonOut bool, w io.Writer) error {
	newPri, err := strconv.Atoi(priorityStr)
	if err != nil {
		return fmt.Errorf("tq: cannot reprioritize task %q: priority must be an integer", id)
	}

	task, err := s.Get(id)
	if err != nil {
		if errors.Is(err, store.ErrNotFound) {
			return fmt.Errorf("tq: cannot reprioritize task %q: not found", id)
		}
		return fmt.Errorf("tq: cannot reprioritize task %q: %w", id, err)
	}
	oldPri := task.Priority

	if err := s.UpdatePriority(id, newPri); err != nil {
		return fmt.Errorf("tq: cannot reprioritize task %q: %w", id, err)
	}

	if jsonOut {
		return json.NewEncoder(w).Encode(PriorityResult{
			ID:          id,
			OldPriority: oldPri,
			NewPriority: newPri,
		})
	}
	fmt.Fprintf(w, "%s\t%d -> %d\n", id, oldPri, newPri)
	return nil
}
