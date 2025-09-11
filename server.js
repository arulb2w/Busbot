// server.js
import express from "express";
import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";
import { fetchAbhiBusServices } from "./busService.js";

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

// Fix __dirname in ES module
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Middleware
app.use(express.json());
app.use(express.static(path.join(__dirname, "public"))); // serve index.html, css, js

// API endpoint for bus search
app.post("/api/search", async (req, res) => {
  try {
    const { fromCity, toCity, travelDate, sortOrder } = req.body;
    if (!fromCity || !toCity || !travelDate) {
      return res.status(400).json({ error: "Missing parameters" });
    }

    const result = await fetchAbhiBusServices(
      fromCity,
      toCity,
      travelDate,
      sortOrder || "fare"
    );
    res.json({ result });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Server running on http://localhost:${PORT}`);
});
