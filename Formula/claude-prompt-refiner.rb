class ClaudePromptRefiner < Formula
  desc "Developer-native TUI for refining prompts using Claude Code"
  homepage "https://github.com/richeshgupta/claude-prompt-refiner"
  url "https://files.pythonhosted.org/packages/source/c/claude-prompt-refiner/claude-prompt-refiner-1.0.0.tar.gz"
  # sha256 will be updated after first PyPI publish
  sha256 "PLACEHOLDER_FILL_AFTER_FIRST_PYPI_PUBLISH"
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
