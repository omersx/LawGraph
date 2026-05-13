import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  ListToolsRequestSchema,
  CallToolRequestSchema
} from "@modelcontextprotocol/sdk/types.js";

import axios from "axios";

const API_KEY = "ZPF8OXnMAh0W1OxVw06EcOP6rECttR8fI6xoW5Dx";
const BASE_URL = "https://api.govinfo.gov";

function simplifyPackages(packages = []) {
  return packages.map((p) => ({
    id: p.packageId || null,
    title: p.title || null,
    date: p.dateIssued || null,
    collection: p.collectionCode || null,
    link: p.packageLink || null
  }));
}

function extractSectionsFromXml(xml) {
  const results = [];

  // common GovInfo bill XML pattern
  const regex =
    /<section[^>]*>[\s\S]*?<enum>(.*?)<\/enum>[\s\S]*?<header>(.*?)<\/header>/g;

  let match;

  while ((match = regex.exec(xml)) !== null && results.length < 15) {
    results.push({
      section: match[1].trim(),
      title: match[2].trim()
    });
  }

  return results;
}

const server = new Server(
  {
    name: "govinfo-mcp",
    version: "2.0.0"
  },
  {
    capabilities: {
      tools: {}
    }
  }
);

//
// LIST TOOLS
//
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "search_documents",
        description:
          "Browse U.S. government documents by collection code such as BILLS, FR, CREC, CFR",
        inputSchema: {
          type: "object",
          properties: {
            collection: {
              type: "string",
              description: "Collection code example BILLS"
            }
          },
          required: ["collection"]
        }
      },

      {
        name: "get_document_details",
        description:
          "Retrieve metadata details for a GovInfo package ID",
        inputSchema: {
          type: "object",
          properties: {
            package_id: {
              type: "string"
            }
          },
          required: ["package_id"]
        }
      },

      {
        name: "get_document_text",
        description:
          "Retrieve text, HTML and XML source links for a document",
        inputSchema: {
          type: "object",
          properties: {
            package_id: {
              type: "string"
            }
          },
          required: ["package_id"]
        }
      },

      {
        name: "extract_bill_sections",
        description:
          "Extract structured sections from bill XML",
        inputSchema: {
          type: "object",
          properties: {
            package_id: {
              type: "string"
            }
          },
          required: ["package_id"]
        }
      }
    ]
  };
});

//
// TOOL CALLS
//
server.setRequestHandler(CallToolRequestSchema, async (request) => {

  const { name, arguments: args } = request.params;

  try {

    //
    // TOOL 1
    //
    if (name === "search_documents") {

      const collection = args.collection || "BILLS";

      const url =
`${BASE_URL}/collections/${collection}?offset=0&pageSize=5&api_key=${API_KEY}`;

      const response = await axios.get(url);

      const packages =
        response.data.packages ||
        response.data.results ||
        [];

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                collection,
                results: simplifyPackages(packages)
              },
              null,
              2
            )
          }
        ]
      };
    }

    //
    // TOOL 2
    //
    if (name === "get_document_details") {

      const url =
`${BASE_URL}/packages/${args.package_id}?api_key=${API_KEY}`;

      const response = await axios.get(url);
      const d = response.data;

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                id: d.packageId,
                title: d.title,
                date: d.dateIssued,
                collection: d.collectionCode,
                link: d.packageLink
              },
              null,
              2
            )
          }
        ]
      };
    }

    //
    // TOOL 3
    //
    if (name === "get_document_text") {

      const url =
`${BASE_URL}/packages/${args.package_id}?api_key=${API_KEY}`;

      const response = await axios.get(url);
      const d = response.data;

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                package_id: d.packageId,
                title: d.title,
                text_sources: {
                  pdf:
                    d.download?.pdfLink || null,
                  html:
                    d.download?.txtLink ||
                    d.download?.htmlLink ||
                    null,
                  xml:
                    d.download?.xmlLink || null
                },
                note:
                  "Use HTML or XML sources for document analysis."
              },
              null,
              2
            )
          }
        ]
      };
    }

    //
    // TOOL 4
    //
    if (name === "extract_bill_sections") {

      const metaUrl =
`${BASE_URL}/packages/${args.package_id}?api_key=${API_KEY}`;

      const metaResponse = await axios.get(metaUrl);

      const xmlLink =
        metaResponse.data.download?.xmlLink;

      if (!xmlLink) {
        return {
          content: [
            {
              type: "text",
              text:
                "No XML source available for this package."
            }
          ]
        };
      }

      const xmlResponse = await axios.get(xmlLink);

      const xml = xmlResponse.data;

      const sections = extractSectionsFromXml(xml);

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                package_id: args.package_id,
                sections_found: sections.length,
                extracted_sections: sections
              },
              null,
              2
            )
          }
        ]
      };
    }

    //
    // UNKNOWN TOOL
    //
    return {
      content: [
        {
          type: "text",
          text: "Unknown tool requested."
        }
      ]
    };

  } catch (err) {

    const details =
      err.response?.data
        ? JSON.stringify(err.response.data, null, 2)
        : err.message;

    return {
      content: [
        {
          type: "text",
          text:
`GovInfo API Error:

${details}`
        }
      ]
    };
  }

});

const transport = new StdioServerTransport();
await server.connect(transport);