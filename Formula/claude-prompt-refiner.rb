class ClaudePromptRefiner < Formula
  desc "Developer-native TUI for refining prompts using Claude Code"
  homepage "https://github.com/richeshgupta/claude-prompt-refiner"
  url "https://files.pythonhosted.org/packages/b7/53/b9e04b90154f01b7c2c16d2a7b30b1056f8a0ea992122c73f84d5234c5da/claude_prompt_refiner-1.0.0.tar.gz"
  sha256 "9fa02d4df1a709554e8f44f34b859f032688a8b18c58fd89df178722eecc0c01"
  license "MIT"
  depends_on "pipx"
  depends_on "python@3.11"

  def install
    system "pipx", "install", "claude-prompt-refiner==#{version}",
           "--python", Formula["python@3.11"].opt_bin/"python3.11",
           "--home", prefix
    bin.install_symlink prefix/"bin/claude-prompt-refiner"
  end

  test do
    output = shell_output("#{bin}/claude-prompt-refiner 2>&1", 1)
    assert_match "claude CLI not found", output
  end
end
