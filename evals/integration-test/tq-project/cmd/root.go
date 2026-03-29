package cmd

import "github.com/spf13/cobra"

var Version = "0.1.0"

var jsonOutput bool

var rootCmd = &cobra.Command{
	Use:   "tq",
	Short: "Local task queue CLI",
}

func init() {
	rootCmd.PersistentFlags().BoolVar(&jsonOutput, "json", false, "Output as JSON")
}

func Execute() error {
	return rootCmd.Execute()
}
