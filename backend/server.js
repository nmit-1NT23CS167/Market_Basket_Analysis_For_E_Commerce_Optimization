const express = require("express");
const cors = require("cors");
const fs = require("fs");
const path = require("path");

const app = express();

// ----------------------
// MIDDLEWARE
// ----------------------
app.use(cors());
app.use(express.json());

// ----------------------
// FILES
// ----------------------
const pairsFile = path.join(__dirname, "data", "pairs.json");
const usersFile = path.join(__dirname, "data", "users.json");

// ----------------------
// INIT FILES
// ----------------------
if (!fs.existsSync(pairsFile)) {
  fs.writeFileSync(pairsFile, JSON.stringify({}));
}

if (!fs.existsSync(usersFile)) {
  fs.writeFileSync(usersFile, JSON.stringify({}));
}

// ----------------------
// UPDATE PAIRS
// ----------------------
function updatePairs(cart) {
  let pairs = JSON.parse(fs.readFileSync(pairsFile));

  for (let i = 0; i < cart.length; i++) {
    for (let j = i + 1; j < cart.length; j++) {
      let key = [cart[i], cart[j]].sort().join("|");
      pairs[key] = (pairs[key] || 0) + 1;
    }
  }

  fs.writeFileSync(pairsFile, JSON.stringify(pairs, null, 2));
}

// ----------------------
// UPDATE USER
// ----------------------
function updateUser(userId, cart) {
  let users = JSON.parse(fs.readFileSync(usersFile));

  if (!users[userId]) {
    users[userId] = [];
  }

  users[userId] = [...new Set([...users[userId], ...cart])];

  fs.writeFileSync(usersFile, JSON.stringify(users, null, 2));
}

// ----------------------
// PLACE ORDER API
// ----------------------
app.post("/order", (req, res) => {

  console.log("📦 RECEIVED:", req.body);

  const { userId, items } = req.body;

  // 🔥 SAFE VALIDATION
  if (
    typeof userId !== "string" ||
    !Array.isArray(items) ||
    items.length === 0
  ) {
    return res.status(400).json({
      error: "Invalid data",
      received: req.body
    });
  }

  console.log("✅ ORDER OK:", userId, items);

  updatePairs(items);
  updateUser(userId, items);

  res.json({
    message: "Order placed successfully",
    userId,
    items
  });
});

// ----------------------
// RECOMMENDATION API
// ----------------------
app.post("/recommend", (req, res) => {

  const { userId, cart } = req.body;

  if (!userId || !Array.isArray(cart)) {
    return res.status(400).json({ error: "Invalid data" });
  }

  const pairs = JSON.parse(fs.readFileSync(pairsFile));
  const users = JSON.parse(fs.readFileSync(usersFile));

  let strong = {};
  for (let key in pairs) {
    if (pairs[key] >= 2) strong[key] = pairs[key];
  }

  let recs = new Set();

  cart.forEach(item => {
    for (let key in strong) {
      let [a, b] = key.split("|");
      if (item === a && !cart.includes(b)) recs.add(b);
      if (item === b && !cart.includes(a)) recs.add(a);
    }
  });

  (users[userId] || []).forEach(item => {
    if (!cart.includes(item)) recs.add(item);
  });

  res.json({ recommendations: Array.from(recs) });
});

// ----------------------
// START SERVER
// ----------------------
app.listen(5000, () => {
  console.log("🚀 Server running on http://localhost:5000");
});