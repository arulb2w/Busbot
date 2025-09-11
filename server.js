require("dotenv").config();
const express = require("express");
const busService = require("./busService");

const app = express();
const PORT = process.env.PORT || 3000;

// Example endpoint: /businfo?from=Chennai&to=Bangalore&date=2025-09-12
app.get("/businfo", async (req, res) => {
  try {
    const { from, to, date } = req.query;

    if (!from || !to || !date) {
      return res.status(400).json({ error: "Missing required parameters" });
    }

    const result = await busService.getBusSchedule(from, to, date);
    res.json(result);

  } catch (err) {
    console.error("Error fetching bus info:", err);
    res.status(500).json({ error: "Internal Server Error" });
  }
});

app.listen(PORT, () => {
  console.log(`🚀 Server running at http://localhost:${PORT}`);
});
