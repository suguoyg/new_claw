import asyncio
import json
from typing import Dict, Callable, Any, Optional
from pathlib import Path
import re

class ToolExecutor:
    """
    Tool Executor - executes tools with safety checks
    """

    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self._register_builtin_tools()

    def _register_builtin_tools(self):
        """Register built-in tools"""
        self.register("file_read", self._file_read)
        self.register("file_write", self._file_write)
        self.register("web_search", self._web_search)
        self.register("command_exec", self._command_exec)
        self.register("load_skill_instructions", self._load_skill_instructions)

    def register(self, name: str, func: Callable):
        """Register a tool"""
        self.tools[name] = func

    def get_tool(self, name: str) -> Optional[Callable]:
        """Get tool by name"""
        return self.tools.get(name)

    def list_tools(self) -> list:
        """List all available tools"""
        return list(self.tools.keys())

    async def execute(self, tool_name: str, params: dict,
                      websocket=None, task_id: str = "") -> dict:
        """Execute a tool directly without user confirmation"""
        tool = self.get_tool(tool_name)
        if not tool:
            return {
                "status": "error",
                "error": f"Tool not found: {tool_name}"
            }

        # Execute tool directly
        try:
            result = await tool(params)
            return {
                "status": "success",
                "result": result
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def _check_safety(self, tool_name: str, params: dict) -> dict:
        """Check if tool execution is safe"""
        if tool_name == "command_exec":
            command = params.get("command", "")
            # Check for dangerous commands
            dangerous_patterns = [
                r"rm\s+-rf\s+/",
                r"mkfs",
                r"dd\s+if=.*of=/dev/",
                r"format\s+",
                r"shred\s+",
            ]

            for pattern in dangerous_patterns:
                if re.search(pattern, command):
                    return {
                        "safe": False,
                        "action": "Execute dangerous command",
                        "target": command[:100],
                        "warning": f"Dangerous command detected: {command[:50]}..."
                    }

            # Check for file modification commands
            modify_patterns = [r"rm\s+", r"del\s+", r">\s*/"]
            for pattern in modify_patterns:
                if re.search(pattern, command):
                    return {
                        "safe": False,
                        "action": "Modify system",
                        "target": command[:100],
                        "warning": "This command may modify system files. Confirm?"
                    }

        elif tool_name == "file_write":
            path = params.get("path", "")
            # Check for system directories
            system_dirs = ["/etc/", "/system/", "/boot/"]
            for sys_dir in system_dirs:
                if path.startswith(sys_dir):
                    return {
                        "safe": False,
                        "action": "Write to system directory",
                        "target": path,
                        "warning": f"Writing to system directory: {path}"
                    }

        return {"safe": True}

    async def _file_read(self, params: dict) -> dict:
        """File read tool"""
        path = params.get("path")
        if not path:
            return {"error": "path is required"}

        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return {"content": content, "path": path}
        except Exception as e:
            return {"error": str(e)}

    async def _file_write(self, params: dict) -> dict:
        """File write tool"""
        path = params.get("path")
        content = params.get("content", "")

        if not path:
            return {"error": "path is required"}

        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"status": "success", "path": path, "bytes_written": len(content)}
        except Exception as e:
            return {"error": str(e)}

    async def _web_search(self, params: dict) -> dict:
        """Web search tool with configurable provider (default: Baidu)"""
        query = params.get("query")
        if not query:
            return {"error": "query is required"}

        # Try multiple search providers
        providers_to_try = [
            ("baidu", "https://www.baidu.com/s", "GET", {"wd": query}),
            ("sogou", "https://www.sogou.com/web", "GET", {"query": query}),
            ("bing", "https://www.bing.com/search", "GET", {"q": query}),
        ]

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }

        import httpx
        for provider, url, method, params_dict in providers_to_try:
            try:
                async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=headers) as client:
                    if method == "GET":
                        response = await client.get(url, params=params_dict)
                    else:
                        response = await client.post(url, data=params_dict)

                    if response.status_code != 200:
                        continue

                    # Skip if blocked by captcha
                    if any(x in response.text for x in ['百度安全验证', '安全验证', 'captcha', 'Belépés']):
                        continue

                    # Try to parse results
                    if provider == "baidu":
                        results = self._parse_baidu_results(response.text)
                    elif provider == "sogou":
                        results = self._parse_sogou_results(response.text)
                    elif provider == "bing":
                        results = self._parse_bing_results(response.text)
                    else:
                        continue

                    if results:
                        return {
                            "results": results[:10],
                            "query": query,
                            "provider": provider,
                            "count": len(results)
                        }

            except Exception:
                continue

        return {"error": "Search service temporarily unavailable. Please try again later."}

    def _load_search_config(self) -> dict:
        """Load search configuration from models.json"""
        try:
            config_file = Path("~/.new_claw/config/models.json").expanduser()
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if "search" in config:
                        return config["search"]
        except Exception:
            pass
        return {"default": "baidu", "providers": {"baidu": {"api_url": "https://www.baidu.com/s", "enabled": True}}}

    def _parse_baidu_results(self, html: str) -> list:
        """Parse Baidu search results"""
        from html.parser import HTMLParser

        class BaiduParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.results = []
                self.in_title = False
                self.in_abstract = False
                self.in_link = False
                self.current_title = ""
                self.current_abstract = ""
                self.current_url = ""
                self.capture = ""
                self.depth = 0

            def handle_starttag(self, tag, attrs):
                attrs_dict = dict(attrs)
                if tag == "h3" and "class" in attrs_dict and "t" in attrs_dict.get("class", ""):
                    self.in_title = True
                    self.current_title = ""
                elif tag == "div" and "class" in attrs_dict and "c-abstract" in attrs_dict.get("class", ""):
                    self.in_abstract = True
                    self.current_abstract = ""
                elif tag == "a" and self.in_title:
                    self.in_link = True
                    self.current_url = attrs_dict.get("href", "")

            def handle_endtag(self, tag):
                if tag == "h3" and self.in_title:
                    self.in_title = False
                elif tag == "div" and self.in_abstract:
                    self.in_abstract = False
                elif tag == "a" and self.in_link:
                    self.in_link = False

            def handle_data(self, data):
                if self.in_title:
                    self.current_title += data
                elif self.in_abstract:
                    self.current_abstract += data

            def handle_charref(self, name):
                if self.in_title:
                    self.current_title += chr(int(name[1:], 16)) if name.startswith('x') else chr(int(name))

        parser = BaiduParser()
        try:
            parser.feed(html)
        except Exception:
            pass

        # Baidu results come as h3+div pairs
        results = []
        titles = []
        abstracts = []
        urls = []

        # Re-parse with simpler approach
        import re
        # Extract title/link pairs
        pattern = r'<h3 class="t"><a[^>]*href="([^"]*)"[^>]*>(.*?)</a></h3>'
        for match in re.finditer(pattern, html, re.DOTALL):
            url = match.group(1)
            title_html = match.group(2)
            # Clean title
            title = re.sub(r'<[^>]+>', '', title_html)
            title = title.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
            titles.append(title.strip())
            urls.append(url.strip())

        # Extract abstracts
        abstract_pattern = r'<div class="c-abstract"[^>]*>.*?<span[^>]*>(.*?)</span>.*?</div>'
        for match in re.finditer(abstract_pattern, html, re.DOTALL):
            abstract_html = match.group(1)
            abstract = re.sub(r'<[^>]+>', '', abstract_html)
            abstract = abstract.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
            abstracts.append(abstract.strip())

        # Combine
        for i in range(min(len(titles), len(urls))):
            results.append({
                "title": titles[i],
                "url": urls[i],
                "snippet": abstracts[i] if i < len(abstracts) else ""
            })

        return results

    def _parse_sogou_results(self, html: str) -> list:
        """Parse Sogou search results"""
        import re

        results = []
        # Sogou result pattern
        pattern = r'<h3[^>]*class="[^"]*pt-p1[^"]*"[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>'
        matches = re.findall(pattern, html, re.DOTALL)

        for url, title_html in matches[:10]:
            title = re.sub(r'<[^>]+>', '', title_html)
            title = title.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
            results.append({
                "title": title.strip(),
                "url": url.strip(),
                "snippet": ""
            })

        # Alternative pattern for Sogou
        if not results:
            pattern = r'<a[^>]*class="[^"]*vr-title[^"]*"[^>]*href="([^"]*)"[^>]*>(.*?)</a>'
            matches = re.findall(pattern, html, re.DOTALL)
            for url, title_html in matches[:10]:
                title = re.sub(r'<[^>]+>', '', title_html)
                results.append({
                    "title": title.strip(),
                    "url": url.strip(),
                    "snippet": ""
                })

        return results

    def _parse_bing_results(self, html: str) -> list:
        """Parse Bing search results"""
        import re

        results = []
        # Bing result pattern
        pattern = r'<li[^>]*class="b_algo[^>]*>.*?<h2[^>]*><a[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?<p[^>]*>(.*?)</p>'
        matches = re.findall(pattern, html, re.DOTALL)

        for url, title_html, snippet_html in matches[:10]:
            title = re.sub(r'<[^>]+>', '', title_html)
            snippet = re.sub(r'<[^>]+>', '', snippet_html)
            results.append({
                "title": title.strip(),
                "url": url.strip(),
                "snippet": snippet.strip()
            })

        return results

    def _parse_ddg_results(self, html: str) -> list:
        """Parse DuckDuckGo search results"""
        from html.parser import HTMLParser

        class DDGParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.results = []
                self.in_result = False
                self.in_title = False
                self.in_snippet = False
                self.current_title = ""
                self.current_snippet = ""
                self.current_url = ""

            def handle_starttag(self, tag, attrs):
                attrs_dict = dict(attrs)
                if tag == "a" and attrs_dict.get("class") == "result__a":
                    self.in_result = True
                    self.current_url = attrs_dict.get("href", "")
                    self.in_title = True
                    self.current_title = ""
                elif tag == "a" and attrs_dict.get("class") == "result__snippet":
                    self.in_snippet = True
                    self.current_snippet = ""

            def handle_endtag(self, tag):
                if tag == "a":
                    if self.in_snippet:
                        self.in_snippet = False
                    elif self.in_result:
                        self.in_result = False
                        if self.current_title and self.current_url:
                            self.results.append({
                                "title": self.current_title.strip(),
                                "url": self.current_url.strip(),
                                "snippet": self.current_snippet.strip()
                            })
                        self.current_title = ""
                        self.current_snippet = ""
                        self.current_url = ""

            def handle_data(self, data):
                if self.in_title and not self.in_snippet:
                    self.current_title += data
                elif self.in_snippet:
                    self.current_snippet += data

        parser = DDGParser()
        try:
            parser.feed(html)
        except Exception:
            pass

        return parser.results

    async def _command_exec(self, params: dict) -> dict:
        """Command execution tool"""
        command = params.get("command")
        if not command:
            return {"error": "command is required"}

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()

            return {
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
                "returncode": proc.returncode
            }
        except Exception as e:
            return {"error": str(e)}

    async def _load_skill_instructions(self, params: dict) -> dict:
        """Load skill instructions on-demand"""
        skill_name = params.get("skill_name")
        if not skill_name:
            return {"error": "skill_name is required"}

        # Build skill path
        skill_path = Path(f"~/.new_claw/skills/{skill_name}").expanduser()
        skill_md_path = skill_path / "SKILL.md"

        if not skill_md_path.exists():
            return {"error": f"Skill not found: {skill_name}"}

        try:
            with open(skill_md_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse YAML frontmatter
            instructions = content
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    instructions = parts[2].strip()

            return {
                "skill_name": skill_name,
                "instructions": instructions,
                "path": str(skill_path)
            }
        except Exception as e:
            return {"error": f"Failed to load skill: {str(e)}"}


# Global executor instance
executor = ToolExecutor()
