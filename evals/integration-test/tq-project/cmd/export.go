package cmd

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"time"

	"tq/store"

	"github.com/spf13/cobra"
)

var exportForce bool

func init() {
	exportCommand.Flags().BoolVar(&exportForce, "force", false, "Overwrite output file if it exists")
	rootCmd.AddCommand(exportCommand)
}

var exportCommand = &cobra.Command{
	Use:   "export <output-file>",
	Short: "Export queue state to a JSON file",
	Args:  cobra.ExactArgs(1),
	RunE:  runExport,
}

func runExport(cmd *cobra.Command, args []string) error {
	s := store.NewMemoryStore()
	defer s.Close()
	return runExportWithStore(s, args[0], exportForce, jsonOutput, os.Stdout)
}

// ExportMetadata is the metadata section of the export file.
type ExportMetadata struct {
	Version    string `json:"version"`
	ExportedAt string `json:"exported_at"`
	TaskCount  int    `json:"task_count"`
}

// ExportTask is the JSON representation of a task in the export file.
type ExportTask struct {
	ID        string   `json:"id"`
	Name      string   `json:"name"`
	Cmd       string   `json:"cmd"`
	State     string   `json:"state"`
	Priority  int      `json:"priority"`
	DependsOn []string `json:"depends_on"`
	CreatedAt string   `json:"created_at"`
}

// ExportData is the top-level structure of the export file.
type ExportData struct {
	Metadata ExportMetadata `json:"metadata"`
	Tasks    []ExportTask   `json:"tasks"`
}

// ExportResult is the JSON stdout feedback for the export command.
type ExportResult struct {
	Path      string `json:"path"`
	TaskCount int    `json:"task_count"`
}

func runExportWithStore(s store.Store, outputPath string, force bool, jsonOut bool, w io.Writer) error {
	// Check if file exists (before doing any work)
	if !force {
		if _, err := os.Stat(outputPath); err == nil {
			return fmt.Errorf("tq: cannot export: file exists (use --force to overwrite)")
		}
	}

	// Retrieve all tasks
	tasks, err := s.List(store.Filter{})
	if err != nil {
		return fmt.Errorf("tq: cannot export: %w", err)
	}

	// Build export tasks
	exportTasks := make([]ExportTask, len(tasks))
	for i, t := range tasks {
		deps := t.DependsOn
		if deps == nil {
			deps = []string{}
		}
		exportTasks[i] = ExportTask{
			ID:        t.ID,
			Name:      t.Name,
			Cmd:       t.Cmd,
			State:     string(t.State),
			Priority:  t.Priority,
			DependsOn: deps,
			CreatedAt: t.CreatedAt.Format(time.RFC3339),
		}
	}

	// Build export data
	data := ExportData{
		Metadata: ExportMetadata{
			Version:    Version,
			ExportedAt: time.Now().UTC().Format(time.RFC3339),
			TaskCount:  len(exportTasks),
		},
		Tasks: exportTasks,
	}

	// Marshal with indentation
	jsonBytes, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return fmt.Errorf("tq: cannot export: %w", err)
	}
	jsonBytes = append(jsonBytes, '\n')

	// Atomic write: temp file + fsync + rename
	dir := filepath.Dir(outputPath)
	tmp, err := os.CreateTemp(dir, ".tq-export-*.tmp")
	if err != nil {
		return fmt.Errorf("tq: cannot export: write %s: %w", outputPath, err)
	}
	tmpName := tmp.Name()

	if _, err := tmp.Write(jsonBytes); err != nil {
		tmp.Close()
		os.Remove(tmpName)
		return fmt.Errorf("tq: cannot export: write %s: %w", outputPath, err)
	}
	if err := tmp.Sync(); err != nil {
		tmp.Close()
		os.Remove(tmpName)
		return fmt.Errorf("tq: cannot export: write %s: %w", outputPath, err)
	}
	if err := tmp.Close(); err != nil {
		os.Remove(tmpName)
		return fmt.Errorf("tq: cannot export: write %s: %w", outputPath, err)
	}
	if err := os.Rename(tmpName, outputPath); err != nil {
		os.Remove(tmpName)
		return fmt.Errorf("tq: cannot export: write %s: %w", outputPath, err)
	}

	// Stdout feedback
	if jsonOut {
		return json.NewEncoder(w).Encode(ExportResult{
			Path:      outputPath,
			TaskCount: len(exportTasks),
		})
	}
	fmt.Fprintf(w, "exported %d tasks to %s\n", len(exportTasks), outputPath)
	return nil
}
