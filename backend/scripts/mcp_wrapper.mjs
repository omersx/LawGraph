/**
 * MCP Server Wrapper — suppresses dotenvx stdout pollution.
 *
 * dotenvx (if globally installed) intercepts dotenv.config() and prints
 * diagnostic messages like "◇ injected env (1) from ..." to stdout.
 * This corrupts the JSONRPC stream used by the MCP stdio protocol.
 *
 * This wrapper temporarily patches process.stdout.write to swallow
 * those messages, then dynamically imports the real MCP server script.
 *
 * Usage:  node scripts/mcp_wrapper.mjs <absolute-path-to-server.js>
 */

const originalWrite = process.stdout.write.bind(process.stdout);

process.stdout.write = (chunk, encoding, callback) => {
  const str = typeof chunk === "string" ? chunk : chunk.toString();

  // Swallow dotenvx diagnostic lines
  if (
    str.includes("injected env") ||
    str.includes("dotenvx") ||
    str.includes("dotenv") && str.includes("tip:")
  ) {
    if (typeof encoding === "function") {
      encoding();          // encoding is actually the callback in this overload
    } else if (typeof callback === "function") {
      callback();
    }
    return true;
  }

  return originalWrite(chunk, encoding, callback);
};

// Resolve the target server path from argv
const serverPath = process.argv[2];
if (!serverPath) {
  process.stderr.write("mcp_wrapper: missing server path argument\n");
  process.exit(1);
}

// Convert Windows backslashes to a proper file:// URL
const fileUrl = "file:///" + serverPath.replace(/\\/g, "/");
await import(fileUrl);
