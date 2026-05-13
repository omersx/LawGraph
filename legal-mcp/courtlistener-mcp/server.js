// NOTE: dotenv removed — env vars are injected by the parent process
// to avoid dotenvx stdout pollution that corrupts the MCP JSONRPC stream


import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import axios from "axios";

// 🔐 API Key
const API_KEY = process.env.COURTLISTENER_API_KEY;

if (!API_KEY) {
  process.stderr.write("Missing COURTLISTENER_API_KEY\n");
  process.exit(1);
}

// ✅ IMPORTANT: use SEARCH API (NOT opinions/?search=)
const BASE_URL = "https://www.courtlistener.com/api/rest/v4";

// Axios instance
const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    Authorization: `Token ${API_KEY}`,
  },
});

// -----------------------------
// Normalize Search Results
// -----------------------------
function simplifySearchResults(results = []) {
  return results.slice(0, 5).map((o) => ({
    cluster_id: o.cluster_id,
    case_name: o.caseName,
    court: o.court,
    court_id: o.court_id,
    date_filed: o.dateFiled,
    citation: o.citation,
    judge: o.judge,
    url: `https://www.courtlistener.com${o.absolute_url}`,
  }));
}

// -----------------------------
// MCP Server
// -----------------------------
const server = new Server(
  {
    name: "courtlistener-mcp",
    version: "2.0.0",
  },
  {
    capabilities: { tools: {} },
  }
);

// -----------------------------
// LIST TOOLS
// -----------------------------
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "search_cases",
        description:
          "Search U.S. court cases with optional filters (court, date, judge)",
        inputSchema: {
          type: "object",
          properties: {
            query: { type: "string" },
            court: {
              type: "string",
              description: "Court ID (e.g., scotus, ca9, dcd)",
            },
            date_from: {
              type: "string",
              description: "Start date YYYY-MM-DD",
            },
            date_to: {
              type: "string",
              description: "End date YYYY-MM-DD",
            },
            judge: {
              type: "string",
              description: "Judge name",
            },
          },
          required: ["query"],
        },
      },
      {
        name: "get_case_details",
        description: "Get full details using cluster_id",
        inputSchema: {
          type: "object",
          properties: {
            cluster_id: { type: "number" },
          },
          required: ["cluster_id"],
        },
      },
    ],
  };
});

// -----------------------------
// HANDLE TOOL CALLS
// -----------------------------
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    // 🔍 SEARCH
    if (name === "search_cases") {
      let url = `/search/?q=${encodeURIComponent(args.query)}`;

      if (args.court) {
        url += `&court=${encodeURIComponent(args.court)}`;
      }

      if (args.date_from) {
        url += `&filed_after=${encodeURIComponent(args.date_from)}`;
      }

      if (args.date_to) {
        url += `&filed_before=${encodeURIComponent(args.date_to)}`;
      }

      if (args.judge) {
        url += `&judge=${encodeURIComponent(args.judge)}`;
      }

      const res = await api.get(url);

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                results: simplifySearchResults(res.data.results || []),
              },
              null,
              2
            ),
          },
        ],
      };
    }

    // 📄 CASE DETAILS (CLUSTER)
    if (name === "get_case_details") {
      const res = await api.get(`/clusters/${args.cluster_id}/`);
      const data = res.data;

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                id: data.id,
                case_name: data.case_name,
                court: data.court,
                date_filed: data.date_filed,
                judges: data.judges,
                citation: data.citation,
                docket: data.docket,
                url: `https://www.courtlistener.com${data.absolute_url}`,
                summary: data.summary,
              },
              null,
              2
            ),
          },
        ],
      };
    }

    return {
      content: [{ type: "text", text: "Unknown tool" }],
    };
  } catch (err) {
    process.stderr.write(`MCP Tool Error: ${JSON.stringify(err.response?.data || err.message)}\n`);

    return {
      content: [
        {
          type: "text",
          text: `Error: ${err.response?.status || ""}\n${
            JSON.stringify(err.response?.data, null, 2) || err.message
          }`,
        },
      ],
    };
  }
});

// -----------------------------
// START SERVER
// -----------------------------
const transport = new StdioServerTransport();
await server.connect(transport);