import express from "express";
import cors from "cors";
import pg from "pg";

const app = express();
const PORT = 5000;

app.use(cors());
app.use(express.json());

const pool = new pg.Pool({
  user: "postgres",       
  host: "localhost",
  database: "stadvdb_db", 
  password: "postgres",    
  port: 5431,
});

function normalizeCountry(c) {
  return c?.toLowerCase()?.trim() || "all countries";
}

app.get("/api/occupancy-by-country", async (req, res) => {
  try {
    const query = `
      SELECT 
        CASE 
          WHEN GROUPING(c.country_name) = 1 THEN 'ALL COUNTRIES'
          ELSE c.country_name 
        END AS country_name,
        CASE 
          WHEN GROUPING(d.month) = 1 THEN 'ALL MONTHS'
          ELSE TO_CHAR(d.month, 'FM00')
        END AS month,
        ROUND(AVG(m.occupancy)::numeric, 2) AS avg_occupancy
      FROM monthly_airbnb m
      JOIN date d ON m.date_id = d.date_id
      JOIN country c ON m.country_id = c.country_id
      GROUP BY ROLLUP (c.country_name, d.month)
      ORDER BY c.country_name, d.month;
    `;
    const result = await pool.query(query);
    res.json(result.rows);
  } catch (err) {
    console.error("/api/occupancy-by-country error:", err);
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/occupancy-vs-temp", async (req, res) => {
  try {
    const query = `
      WITH monthly_occupancy AS (
        SELECT 
            m.country_id,
            d.month,
            ROUND(AVG(m.occupancy)::numeric, 2) AS avg_occupancy
        FROM monthly_airbnb m
        JOIN date d ON m.date_id = d.date_id
        GROUP BY m.country_id, d.month
      )
      SELECT 
          CASE WHEN GROUPING(c.country_name) = 1 THEN 'ALL COUNTRIES' ELSE c.country_name END AS country_name,
          CASE WHEN GROUPING(w.month) = 1 THEN 'ALL MONTHS' ELSE TO_CHAR(w.month, 'FM00') END AS month,
          ROUND(AVG(w.mean_temp)::numeric, 1) AS avg_temp,
          ROUND(AVG(mo.avg_occupancy)::numeric, 2) AS avg_occupancy
      FROM weather_normals w
      JOIN country c ON w.country_id = c.country_id
      LEFT JOIN monthly_occupancy mo ON w.country_id = mo.country_id AND w.month = mo.month
      GROUP BY ROLLUP (c.country_name, w.month)
      ORDER BY c.country_name, w.month;
    `;
    const result = await pool.query(query);
    res.json(result.rows);
  } catch (err) {
    console.error("/api/occupancy-vs-temp error:", err);
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/occupancy-by-type", async (req, res) => {
  try {
    const query = `
      SELECT 
        CASE WHEN GROUPING(c.country_name) = 1 THEN 'ALL COUNTRIES' ELSE c.country_name END AS country_name,
        CASE WHEN GROUPING(a.listing_type) = 1 THEN 'ALL TYPES' ELSE a.listing_type END AS listing_type,
        ROUND(AVG(m.occupancy)::numeric, 2) AS avg_occupancy,
        COUNT(DISTINCT m.listing_id) AS listing_count
      FROM monthly_airbnb m
      JOIN airbnb_listing a ON m.listing_id = a.listing_id
      JOIN country c ON m.country_id = c.country_id
      GROUP BY ROLLUP (c.country_name, a.listing_type)
      ORDER BY c.country_name, a.listing_type;
    `;
    const result = await pool.query(query);
    res.json(result.rows);
  } catch (err) {
    console.error("/api/occupancy-by-type error:", err);
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/occupancy-by-rating", async (req, res) => {
  try {
    const query = `
      WITH rating_band AS (
        SELECT 
            a.listing_id,
            a.country_id,
            a.room_type,
            CASE 
                WHEN a.rating_overall >= 4.5 THEN 'Excellent (4.5–5.0)'
                WHEN a.rating_overall >= 4.0 THEN 'Good (4.0–4.49)'
                WHEN a.rating_overall >= 3.0 THEN 'Average (3.0–3.99)'
                WHEN a.rating_overall IS NULL THEN 'Unrated'
                ELSE 'Low (<3.0)'
            END AS rating_group
        FROM airbnb_listing a
      )
      SELECT 
          CASE WHEN GROUPING(r.rating_group) = 1 THEN 'ALL RATING GROUPS' ELSE r.rating_group END AS rating_group,
          CASE WHEN GROUPING(c.country_name) = 1 THEN 'ALL COUNTRIES' ELSE c.country_name END AS country_name,
          CASE WHEN GROUPING(r.room_type) = 1 THEN 'ALL ROOM TYPES' ELSE r.room_type END AS room_type,
          ROUND(AVG(m.occupancy)::numeric, 2) AS avg_occupancy,
          COUNT(DISTINCT m.listing_id) AS listing_count
      FROM monthly_airbnb m
      JOIN rating_band r ON m.listing_id = r.listing_id
      JOIN country c ON m.country_id = c.country_id
      GROUP BY ROLLUP (r.rating_group, c.country_name, r.room_type)
      ORDER BY r.rating_group, c.country_name, r.room_type;
    `;
    const result = await pool.query(query);
    res.json(result.rows);
  } catch (err) {
    console.error("/api/occupancy-by-rating error:", err);
    res.status(500).json({ error: err.message });
  }
});

app.get("/api/tourism-rollup", async (req, res) => {
  try {
    const query = `
      SELECT 
        CASE WHEN GROUPING(c.country_name) = 1 THEN 'ALL COUNTRIES' ELSE c.country_name END AS country_name,
        CASE WHEN GROUPING(t.year) = 1 THEN 'ALL YEARS' ELSE t.year::text END AS year,
        SUM(t.total_arrivals) AS total_arrivals,
        SUM(t.total_departures) AS total_departures,
        ROUND(AVG(t.arrivals_personal)::numeric, 0) AS avg_personal_arrivals,
        ROUND(AVG(t.arrivals_business)::numeric, 0) AS avg_business_arrivals
      FROM tourism t
      JOIN country c ON t.country_id = c.country_id
      GROUP BY ROLLUP (c.country_name, t.year)
      ORDER BY c.country_name, t.year;
    `;
    const result = await pool.query(query);
    res.json(result.rows);
  } catch (err) {
    console.error("/api/tourism-rollup error:", err);
    res.status(500).json({ error: err.message });
  }
});



app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
