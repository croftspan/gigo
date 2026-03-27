package cmd

import (
	"bytes"
	"encoding/json"
	"strings"
	"testing"

	"tq/store"
)

func seedStore(tasks []store.Task) *store.MemoryStore {
	s := store.NewMemoryStore()
	for _, t := range tasks {
		s.Add(t)
	}
	return s
}

func TestStatusEmpty(t *testing.T) {
	s := seedStore(nil)
	var buf bytes.Buffer
	if err := runStatusWithStore(s, false, &buf); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	out := buf.String()
	if !strings.Contains(out, "total     0") {
		t.Errorf("expected total 0, got:\n%s", out)
	}
	if !strings.Contains(out, "health    empty") {
		t.Errorf("expected health empty, got:\n%s", out)
	}
}

func TestStatusHealthy(t *testing.T) {
	s := seedStore([]store.Task{
		{Name: "a", State: store.StateReady},
		{Name: "b", State: store.StateRunning},
		{Name: "c", State: store.StateDone},
	})
	var buf bytes.Buffer
	if err := runStatusWithStore(s, false, &buf); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	out := buf.String()
	if !strings.Contains(out, "health    healthy") {
		t.Errorf("expected healthy, got:\n%s", out)
	}
	if !strings.Contains(out, "total     3") {
		t.Errorf("expected total 3, got:\n%s", out)
	}
}

func TestStatusDegraded(t *testing.T) {
	s := seedStore([]store.Task{
		{Name: "a", State: store.StateReady},
		{Name: "b", State: store.StateFailed},
	})
	var buf bytes.Buffer
	runStatusWithStore(s, false, &buf)
	if !strings.Contains(buf.String(), "health    degraded") {
		t.Errorf("expected degraded, got:\n%s", buf.String())
	}
}

func TestStatusUnhealthy(t *testing.T) {
	s := seedStore([]store.Task{
		{Name: "a", State: store.StateDead},
	})
	var buf bytes.Buffer
	runStatusWithStore(s, false, &buf)
	if !strings.Contains(buf.String(), "health    unhealthy") {
		t.Errorf("expected unhealthy, got:\n%s", buf.String())
	}
}

func TestStatusIdle(t *testing.T) {
	s := seedStore([]store.Task{
		{Name: "a", State: store.StateDone},
		{Name: "b", State: store.StateDone},
	})
	var buf bytes.Buffer
	runStatusWithStore(s, false, &buf)
	if !strings.Contains(buf.String(), "health    idle") {
		t.Errorf("expected idle, got:\n%s", buf.String())
	}
}

func TestStatusJSON(t *testing.T) {
	s := seedStore([]store.Task{
		{Name: "a", State: store.StateReady},
		{Name: "b", State: store.StatePending},
		{Name: "c", State: store.StateDone},
	})
	var buf bytes.Buffer
	if err := runStatusWithStore(s, true, &buf); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	var out StatusOutput
	if err := json.Unmarshal(buf.Bytes(), &out); err != nil {
		t.Fatalf("invalid JSON: %v\nraw: %s", err, buf.String())
	}
	if out.Ready != 1 {
		t.Errorf("expected ready=1, got %d", out.Ready)
	}
	if out.Total != 3 {
		t.Errorf("expected total=3, got %d", out.Total)
	}
	if out.Health != "healthy" {
		t.Errorf("expected healthy, got %s", out.Health)
	}
}
