package cmd

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"sort"
	"strings"
	"time"

	"tq/store"

	"github.com/spf13/cobra"
)

var listState string

func init() {
	listCommand.Flags().StringVar(&listState, "state", "", "Filter by state (pending, ready, running, done, failed, dead)")
	rootCmd.AddCommand(listCommand)
}

var listCommand = &cobra.Command{
	Use:   "list",
	Short: "List tasks in the queue",
	RunE:  runList,
}

func runList(cmd *cobra.Command, args []string) error {
	s := store.NewMemoryStore()
	defer s.Close()
	return runListWithStore(s, listState, jsonOutput, os.Stdout)
}

// ListTask is the JSON representation of a task in list output.
type ListTask struct {
	ID        string   `json:"id"`
	Name      string   `json:"name"`
	Cmd       string   `json:"cmd"`
	State     string   `json:"state"`
	Priority  int      `json:"priority"`
	DependsOn []string `json:"depends_on"`
	CreatedAt string   `json:"created_at"`
}

func runListWithStore(s store.Store, stateStr string, jsonOut bool, w io.Writer) error {
	var filter store.Filter
	if stateStr != "" {
		st := store.State(stateStr)
		valid := false
		for _, s := range store.AllStates {
			if s == st {
				valid = true
				break
			}
		}
		if !valid {
			names := make([]string, len(store.AllStates))
			for i, s := range store.AllStates {
				names[i] = string(s)
			}
			return fmt.Errorf("tq: invalid state %q (valid: %s)", stateStr, strings.Join(names, ", "))
		}
		filter.State = &st
	}

	tasks, err := s.List(filter)
	if err != nil {
		return fmt.Errorf("tq: cannot list tasks: %w", err)
	}

	// Sort: priority descending, then CreatedAt ascending
	sort.Slice(tasks, func(i, j int) bool {
		if tasks[i].Priority != tasks[j].Priority {
			return tasks[i].Priority > tasks[j].Priority
		}
		return tasks[i].CreatedAt.Before(tasks[j].CreatedAt)
	})

	if jsonOut {
		out := make([]ListTask, len(tasks))
		for i, t := range tasks {
			deps := t.DependsOn
			if deps == nil {
				deps = []string{}
			}
			out[i] = ListTask{
				ID:        t.ID,
				Name:      t.Name,
				Cmd:       t.Cmd,
				State:     string(t.State),
				Priority:  t.Priority,
				DependsOn: deps,
				CreatedAt: t.CreatedAt.Format(time.RFC3339),
			}
		}
		return json.NewEncoder(w).Encode(out)
	}

	if len(tasks) == 0 {
		return nil
	}

	fmt.Fprintf(w, "%-10s%-10s%4s  %-16s%s\n", "ID", "STATE", "PRI", "NAME", "DEPENDS")
	for _, t := range tasks {
		deps := strings.Join(t.DependsOn, ",")
		fmt.Fprintf(w, "%-10s%-10s%4d  %-16s%s\n", t.ID, t.State, t.Priority, t.Name, deps)
	}
	return nil
}
