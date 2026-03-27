package cmd

import (
	"encoding/json"
	"fmt"
	"os"

	"tq/store"

	"github.com/spf13/cobra"
)

type StatusOutput struct {
	Pending int    `json:"pending"`
	Ready   int    `json:"ready"`
	Running int    `json:"running"`
	Done    int    `json:"done"`
	Failed  int    `json:"failed"`
	Dead    int    `json:"dead"`
	Total   int    `json:"total"`
	Health  string `json:"health"`
}

func init() {
	rootCmd.AddCommand(statusCmd)
}

var statusCmd = &cobra.Command{
	Use:   "status",
	Short: "Show queue status",
	RunE:  runStatus,
}

func runStatus(cmd *cobra.Command, args []string) error {
	s := store.NewMemoryStore()
	defer s.Close()

	tasks, err := s.List(store.Filter{})
	if err != nil {
		return fmt.Errorf("tq: cannot read queue status: %w", err)
	}

	counts := make(map[store.State]int)
	for _, t := range tasks {
		counts[t.State]++
	}

	total := len(tasks)
	h := health(counts, total)

	out := StatusOutput{
		Pending: counts[store.StatePending],
		Ready:   counts[store.StateReady],
		Running: counts[store.StateRunning],
		Done:    counts[store.StateDone],
		Failed:  counts[store.StateFailed],
		Dead:    counts[store.StateDead],
		Total:   total,
		Health:  h,
	}

	if jsonOutput {
		return json.NewEncoder(os.Stdout).Encode(out)
	}

	for _, state := range store.AllStates {
		fmt.Fprintf(os.Stdout, "%-10s%d\n", state, counts[state])
	}
	fmt.Fprintf(os.Stdout, "%-10s%d\n", "total", total)
	fmt.Fprintf(os.Stdout, "%-10s%s\n", "health", h)

	return nil
}

func health(counts map[store.State]int, total int) string {
	switch {
	case total == 0:
		return "empty"
	case counts[store.StateDead] > 0:
		return "unhealthy"
	case counts[store.StateFailed] > 0:
		return "degraded"
	case counts[store.StateRunning] == 0 && counts[store.StateReady] == 0 && counts[store.StateDone] > 0:
		return "idle"
	default:
		return "healthy"
	}
}
