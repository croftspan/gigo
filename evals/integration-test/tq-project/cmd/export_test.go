package cmd

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"tq/store"
)

func TestExport(t *testing.T) {
	s := seedStore([]store.Task{
		{ID: "aaaa1111", Name: "build", Cmd: "make build", State: store.StateReady, Priority: 5, DependsOn: []string{}, CreatedAt: time.Date(2026, 3, 28, 10, 0, 0, 0, time.UTC)},
		{ID: "bbbb2222", Name: "test", Cmd: "make test", State: store.StatePending, Priority: 3, DependsOn: []string{"aaaa1111"}, CreatedAt: time.Date(2026, 3, 28, 11, 0, 0, 0, time.UTC)},
	})

	dir := t.TempDir()
	outPath := filepath.Join(dir, "export.json")
	var buf bytes.Buffer

	err := runExportWithStore(s, outPath, false, false, &buf)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	// Check stdout feedback
	if !strings.Contains(buf.String(), "exported 2 tasks to") {
		t.Errorf("expected feedback message, got: %q", buf.String())
	}

	// Read and parse export file
	data, err := os.ReadFile(outPath)
	if err != nil {
		t.Fatalf("cannot read export file: %v", err)
	}

	var export ExportData
	if err := json.Unmarshal(data, &export); err != nil {
		t.Fatalf("invalid JSON in export file: %v\nraw: %s", err, data)
	}

	// Check metadata
	if export.Metadata.Version != Version {
		t.Errorf("expected version %q, got %q", Version, export.Metadata.Version)
	}
	if export.Metadata.TaskCount != 2 {
		t.Errorf("expected task_count 2, got %d", export.Metadata.TaskCount)
	}
	if _, err := time.Parse(time.RFC3339, export.Metadata.ExportedAt); err != nil {
		t.Errorf("exported_at is not valid RFC3339: %q", export.Metadata.ExportedAt)
	}

	// Check tasks
	if len(export.Tasks) != 2 {
		t.Fatalf("expected 2 tasks, got %d", len(export.Tasks))
	}
}

func TestExportJSON(t *testing.T) {
	s := seedStore([]store.Task{
		{ID: "aaaa1111", Name: "build", Cmd: "make", State: store.StateReady, Priority: 5, DependsOn: []string{}, CreatedAt: time.Now()},
		{ID: "bbbb2222", Name: "test", Cmd: "make test", State: store.StateDone, Priority: 3, DependsOn: []string{}, CreatedAt: time.Now()},
	})

	dir := t.TempDir()
	outPath := filepath.Join(dir, "export.json")
	var buf bytes.Buffer

	err := runExportWithStore(s, outPath, false, true, &buf)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	var result ExportResult
	if err := json.Unmarshal(buf.Bytes(), &result); err != nil {
		t.Fatalf("invalid JSON stdout: %v\nraw: %s", err, buf.String())
	}
	if result.TaskCount != 2 {
		t.Errorf("expected task_count 2, got %d", result.TaskCount)
	}
	if result.Path != outPath {
		t.Errorf("expected path %q, got %q", outPath, result.Path)
	}
}

func TestExportFileExists(t *testing.T) {
	s := store.NewMemoryStore()

	dir := t.TempDir()
	outPath := filepath.Join(dir, "export.json")
	os.WriteFile(outPath, []byte("existing"), 0644)

	var buf bytes.Buffer
	err := runExportWithStore(s, outPath, false, false, &buf)
	if err == nil {
		t.Fatal("expected error for existing file")
	}
	if !strings.Contains(err.Error(), "file exists (use --force to overwrite)") {
		t.Errorf("expected file-exists error, got: %v", err)
	}
}

func TestExportFileExistsForce(t *testing.T) {
	s := seedStore([]store.Task{
		{ID: "aaaa1111", Name: "build", Cmd: "make", State: store.StateReady, Priority: 5, DependsOn: []string{}, CreatedAt: time.Now()},
	})

	dir := t.TempDir()
	outPath := filepath.Join(dir, "export.json")
	os.WriteFile(outPath, []byte("existing"), 0644)

	var buf bytes.Buffer
	err := runExportWithStore(s, outPath, true, false, &buf)
	if err != nil {
		t.Fatalf("unexpected error with --force: %v", err)
	}

	// Verify file was overwritten with valid export
	data, err := os.ReadFile(outPath)
	if err != nil {
		t.Fatalf("cannot read export file: %v", err)
	}
	var export ExportData
	if err := json.Unmarshal(data, &export); err != nil {
		t.Fatalf("invalid JSON after --force overwrite: %v", err)
	}
	if export.Metadata.TaskCount != 1 {
		t.Errorf("expected task_count 1, got %d", export.Metadata.TaskCount)
	}
}

func TestExportEmptyQueue(t *testing.T) {
	s := store.NewMemoryStore()

	dir := t.TempDir()
	outPath := filepath.Join(dir, "export.json")
	var buf bytes.Buffer

	err := runExportWithStore(s, outPath, false, false, &buf)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	data, err := os.ReadFile(outPath)
	if err != nil {
		t.Fatalf("cannot read export file: %v", err)
	}
	var export ExportData
	if err := json.Unmarshal(data, &export); err != nil {
		t.Fatalf("invalid JSON: %v", err)
	}
	if export.Metadata.TaskCount != 0 {
		t.Errorf("expected task_count 0, got %d", export.Metadata.TaskCount)
	}
	if len(export.Tasks) != 0 {
		t.Errorf("expected empty tasks array, got %d tasks", len(export.Tasks))
	}
}

func TestExportDependsOnNeverNull(t *testing.T) {
	s := seedStore([]store.Task{
		{ID: "aaaa1111", Name: "no-deps", Cmd: "echo 1", State: store.StateReady, Priority: 1, CreatedAt: time.Now()},
		{ID: "bbbb2222", Name: "has-deps", Cmd: "echo 2", State: store.StatePending, Priority: 1, DependsOn: []string{"aaaa1111"}, CreatedAt: time.Now()},
	})

	dir := t.TempDir()
	outPath := filepath.Join(dir, "export.json")
	var buf bytes.Buffer

	err := runExportWithStore(s, outPath, false, false, &buf)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	data, err := os.ReadFile(outPath)
	if err != nil {
		t.Fatalf("cannot read export file: %v", err)
	}

	// Check raw JSON — depends_on must be [] not null
	raw := string(data)
	if strings.Contains(raw, `"depends_on": null`) || strings.Contains(raw, `"depends_on":null`) {
		t.Error("depends_on must be [] not null in export JSON")
	}

	// Parse and verify the no-deps task has empty array
	var export ExportData
	json.Unmarshal(data, &export)
	for _, task := range export.Tasks {
		if task.DependsOn == nil {
			t.Errorf("task %q has nil depends_on after unmarshal", task.ID)
		}
	}
}
