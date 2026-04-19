let cart = [];

// DATA (dynamic)
let orders = JSON.parse(localStorage.getItem("orders")) || [
  ["Burger","Pizza"],
  ["Burger","Coke"],
  ["Pizza","Fries"],
  ["Burger","Fries"]
];

// ADD ITEM
function add(name, price){
  cart.push({name, price});
  updateRecommend();
}

// 🔥 SMART RECOMMENDATION
function updateRecommend(){

  let freq = {};

  orders.forEach(order=>{
    cart.forEach(c=>{
      if(order.includes(c.name)){
        order.forEach(item=>{
          if(!cart.map(i=>i.name).includes(item)){
            freq[item] = (freq[item] || 0) + 1;
          }
        });
      }
    });
  });

  let sorted = Object.entries(freq).sort((a,b)=>b[1]-a[1]);

  let box = document.getElementById("recommendBox");

  if(sorted.length > 0){
    box.classList.remove("hidden");
    box.innerHTML = "🔥 Try adding: <b>" + sorted[0][0] + "</b>";
  } else {
    box.classList.add("hidden");
  }
}

// VIEW CART
function viewCart(){

  // HIDE RECOMMEND AFTER CLICK
  document.getElementById("recommendBox").classList.add("hidden");

  let box = document.getElementById("cartBox");
  box.classList.remove("hidden");

  let html = "";
  let total = 0;

  cart.forEach(i=>{
    html += `<p>${i.name} - ₹${i.price}</p>`;
    total += i.price;
  });

  html += `<h3>Total ₹${total}</h3>`;
  html += `<button onclick="placeOrder()">Place Order</button>`;

  box.innerHTML = html;
}

// PLACE ORDER
function placeOrder(){
  let order = cart.map(i=>i.name);
  orders.push(order);

  localStorage.setItem("orders", JSON.stringify(orders));

  alert("Order placed!");
  cart = [];
  location.reload();
}

// LOGOUT
function logout(){
  localStorage.removeItem("user");
  location="auth.html";
}