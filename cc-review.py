#!/usr/bin/env python3
"""
cc-review: A human-forward code review tool for Claude Code outputs
"""

import subprocess
import sys
from dataclasses import dataclass
from typing import List, Optional


class Colors:
    """ANSI color codes for terminal output"""
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ENDC = '\033[0m'
    
    @staticmethod
    def blue(text): return f"{Colors.BLUE}{text}{Colors.ENDC}"
    
    @staticmethod
    def cyan(text): return f"{Colors.CYAN}{text}{Colors.ENDC}"
    
    @staticmethod
    def green(text): return f"{Colors.GREEN}{text}{Colors.ENDC}"
    
    @staticmethod
    def yellow(text): return f"{Colors.YELLOW}{text}{Colors.ENDC}"
    
    @staticmethod
    def red(text): return f"{Colors.RED}{text}{Colors.ENDC}"
    
    @staticmethod
    def bold(text): return f"{Colors.BOLD}{text}{Colors.ENDC}"
    
    @staticmethod
    def dim(text): return f"{Colors.DIM}{text}{Colors.ENDC}"


@dataclass
class DiffHunk:
    """Represents a single hunk (section) of changes in a file"""
    header: str  # e.g., "@@ -10,5 +10,7 @@"
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: List[str]  # The actual diff lines


@dataclass
class FileDiff:
    """Represents all changes to a single file"""
    old_path: str
    new_path: str
    is_new: bool
    is_deleted: bool
    hunks: List[DiffHunk]


class DiffParser:
    """Parses git diff output into structured format"""
    
    def __init__(self, diff_text: str):
        self.diff_text = diff_text
        self.files: List[FileDiff] = []
    
    def parse(self) -> List[FileDiff]:
        """Parse the diff text into FileDiff objects"""
        lines = self.diff_text.split('\n')
        current_file = None
        current_hunk = None
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Start of a new file diff
            if line.startswith('diff --git'):
                if current_file and current_hunk:
                    current_file.hunks.append(current_hunk)
                    current_hunk = None
                if current_file:
                    self.files.append(current_file)
                
                # Parse file paths
                parts = line.split(' ')
                old_path = parts[2][2:]  # Remove 'a/' prefix
                new_path = parts[3][2:]  # Remove 'b/' prefix
                
                current_file = FileDiff(
                    old_path=old_path,
                    new_path=new_path,
                    is_new=False,
                    is_deleted=False,
                    hunks=[]
                )
            
            # Check for new/deleted files
            elif line.startswith('new file mode'):
                if current_file:
                    current_file.is_new = True
            
            elif line.startswith('deleted file mode'):
                if current_file:
                    current_file.is_deleted = True
            
            # Start of a new hunk
            elif line.startswith('@@'):
                if current_hunk and current_file:
                    current_file.hunks.append(current_hunk)
                
                # Parse hunk header: @@ -10,5 +10,7 @@
                parts = line.split('@@')
                if len(parts) >= 2:
                    ranges = parts[1].strip().split(' ')
                    old_range = ranges[0][1:].split(',')  # Remove '-' and split
                    new_range = ranges[1][1:].split(',')  # Remove '+' and split
                    
                    old_start = int(old_range[0])
                    old_count = int(old_range[1]) if len(old_range) > 1 else 1
                    new_start = int(new_range[0])
                    new_count = int(new_range[1]) if len(new_range) > 1 else 1
                    
                    current_hunk = DiffHunk(
                        header=line,
                        old_start=old_start,
                        old_count=old_count,
                        new_start=new_start,
                        new_count=new_count,
                        lines=[]
                    )
            
            # Content lines (additions, deletions, context)
            elif current_hunk is not None:
                if line.startswith('+') or line.startswith('-') or line.startswith(' '):
                    current_hunk.lines.append(line)
            
            i += 1
        
        # Don't forget the last hunk and file
        if current_hunk and current_file:
            current_file.hunks.append(current_hunk)
        if current_file:
            self.files.append(current_file)
        
        return self.files


class DiffDisplay:
    """Handles display of diffs"""
    
    @staticmethod
    def get_file_language(filepath: str) -> str:
        """Determine syntax highlighting language from file extension"""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.c': 'c',
            '.cpp': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.css': 'css',
            '.html': 'html',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.sh': 'bash',
            '.sql': 'sql',
        }
        
        for ext, lang in ext_map.items():
            if filepath.endswith(ext):
                return lang
        return 'text'
    
    @staticmethod
    def display_file_header(file_diff: FileDiff):
        """Display the file header with status"""
        status = ""
        if file_diff.is_new:
            status = f" {Colors.green('(new file)')}"
        elif file_diff.is_deleted:
            status = f" {Colors.red('(deleted)')}"
        elif file_diff.old_path != file_diff.new_path:
            status = f" {Colors.yellow(f'(renamed from {file_diff.old_path})')}"
        
        print(f"\n{Colors.bold(Colors.blue('File:'))} {file_diff.new_path}{status}")
        print("─" * 80)
    
    @staticmethod
    def display_hunk(hunk: DiffHunk, file_path: str):
        """Display a single hunk"""
        print(f"\n{Colors.dim(hunk.header)}")
        
        # Display the diff lines with appropriate colors
        for line in hunk.lines:
            if line.startswith('+'):
                print(Colors.green(line))
            elif line.startswith('-'):
                print(Colors.red(line))
            else:
                print(Colors.dim(line))
    
    @staticmethod
    def display_summary(files: List[FileDiff]):
        """Display a summary of all changes"""
        total_files = len(files)
        new_files = sum(1 for f in files if f.is_new)
        deleted_files = sum(1 for f in files if f.is_deleted)
        modified_files = total_files - new_files - deleted_files
        
        total_hunks = sum(len(f.hunks) for f in files)
        
        print("\n" + "=" * 80)
        print(Colors.bold(Colors.cyan("Diff Summary")))
        print("=" * 80)
        print(f"\nFiles changed: {total_files}")
        print(f"  - Modified: {modified_files}")
        print(f"  - New: {Colors.green(str(new_files))}")
        print(f"  - Deleted: {Colors.red(str(deleted_files))}")
        print(f"Total sections: {total_hunks}")
        print("=" * 80)


def get_git_diff(ref: Optional[str] = None) -> str:
    """Get git diff output"""
    try:
        if ref:
            # Compare against a specific ref
            cmd = ['git', 'diff', ref]
        else:
            # Compare working tree to HEAD
            cmd = ['git', 'diff', 'HEAD']
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"{Colors.red('Error running git diff:')} {e.stderr}")
        sys.exit(1)


def main():
    """Main entry point"""
    print(f"{Colors.bold(Colors.cyan('cc-review'))} - Code Review Tool\n")
    
    # Get reference from command line if provided
    ref = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Get the diff
    print(Colors.dim("Fetching diff..."))
    diff_text = get_git_diff(ref)
    
    if not diff_text.strip():
        print(Colors.yellow("No changes to review!"))
        sys.exit(0)
    
    # Parse the diff
    parser = DiffParser(diff_text)
    files = parser.parse()
    
    # Display summary
    DiffDisplay.display_summary(files)
    
    # Display each file's changes
    for file_diff in files:
        DiffDisplay.display_file_header(file_diff)
        
        for hunk in file_diff.hunks:
            DiffDisplay.display_hunk(hunk, file_diff.new_path)
    
    print(f"\n{Colors.green('✓')} Review complete!")


if __name__ == "__main__":
    main()
