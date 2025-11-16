// mockGraphData.ts
import type { NodeDatum, EdgeDatum } from "./types";

const mockGraphData = {
  repoANodes: [
    { id: "topic_payment", repo: "repoA", type: "TOPIC", name: "Topic Payment" },
    { id: "topic_orders", repo: "repoA", type: "TOPIC", name: "Topic Orders" },
    { id: "service_a1", repo: "repoA", type: "SERVICE", name: "Service A1" },
    { id: "service_a2", repo: "repoA", type: "SERVICE", name: "service A2" },
  ],
  repoBNodes: [
    { id: "consumer1", repo: "repoB", type: "FUNCTION", name: "Consumer 1" },
    { id: "service_b1", repo: "repoB", type: "SERVICE", name: "service B1" },
    { id: "service_b2", repo: "repoB", type: "SERVICE", name: "service B2" },
  ],
  repoCNodes: [
    { id: "util_x", repo: "repoC", type: "SERVICE", name: "Util X" },
    { id: "util_y", repo: "repoC", type: "SERVICE", name: "Util Y" },
  ],

  edges: [
    // A Intra
    { from: "topic_payment", to: "service_a1", type: "READS" },
    { from: "topic_payment", to: "topic_orders", type: "DEPENDS_ON" },
    { from: "service_a1", to: "service_a2", type: "CALLS" },

    // B Intra
    { from: "consumer1", to: "service_b1", type: "CALLS" },
    { from: "service_b1", to: "service_b2", type: "CALLS" },

    // C Intra
    { from: "util_x", to: "util_y", type: "CALLS" },

    // A → B
    { from: "service_a1", to: "service_b1", type: "CALLS" },
    { from: "topic_orders", to: "consumer1", type: "WRITES" },

    // B → C
    { from: "service_b2", to: "util_x", type: "CALLS" },
  ],
};

export default mockGraphData;
