function closeAllDropdowns() {
  document.querySelectorAll(".dropdown-menu").forEach(m => m.dataset.open = "false");
}

document.addEventListener("click", (e) => {
  const trigger = e.target.closest(".dropdown-trigger");
  const menu = e.target.closest(".dropdown-menu");

  if (trigger) {
    const root = trigger.closest(".dropdown");
    const m = root.querySelector(".dropdown-menu");
    const isOpen = m.dataset.open === "true";
    closeAllDropdowns();
    m.dataset.open = isOpen ? "false" : "true";
    return;
  }
  if (!menu) closeAllDropdowns();
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeAllDropdowns();
});

function mkChart(id, config) {
  const el = document.getElementById(id);
  if (!el || !window.Chart) return;
  // eslint-disable-next-line no-new
  new Chart(el.getContext("2d"), config);
}

function paceCharts() {
  const grid = "rgba(241,245,249,0.08)";
  const axis = "#94A3B8";

  const common = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { labels: { color: axis } },
      tooltip: {
        backgroundColor: "rgba(14,16,44,0.95)",
        borderColor: "rgba(241,245,249,0.14)",
        borderWidth: 1,
        titleColor: "#F1F5F9",
        bodyColor: "#F1F5F9"
      }
    },
    scales: {
      x: { grid: { color: grid }, ticks: { color: axis } },
      y: { grid: { color: grid }, ticks: { color: axis } }
    }
  };

  mkChart("riskDist", {
    type: "bar",
    data: {
      labels: ["0-20", "21-40", "41-60", "61-80", "81-100"],
      datasets: [{
        label: "Shipments",
        data: [42, 88, 120, 74, 31],
        backgroundColor: ["#10B981", "#10B981", "#F59E0B", "#EF4444", "#EF4444"]
      }]
    },
    options: { ...common }
  });

  mkChart("riskByCarrier", {
    type: "bar",
    data: {
      labels: ["Carrier A", "Carrier B", "Carrier C", "Carrier D", "Carrier E"],
      datasets: [{
        label: "Avg Risk (%)",
        data: [28, 36, 44, 62, 73],
        backgroundColor: "#563457"
      }]
    },
    options: {
      ...common,
      indexAxis: "y",
      scales: {
        x: { grid: { color: grid }, ticks: { color: axis }, suggestedMax: 100 },
        y: { grid: { color: "rgba(0,0,0,0)" }, ticks: { color: axis } }
      }
    }
  });

  mkChart("tierBreakdown", {
    type: "bar",
    data: {
      labels: ["Low", "Medium", "High"],
      datasets: [
        { label: "Shipments", data: [210, 140, 52], backgroundColor: "#1B435E" },
        { label: "Est. Cost ($k)", data: [38, 64, 88], backgroundColor: "#2DD4BF" }
      ]
    },
    options: { ...common }
  });

  mkChart("shipmentsOverTime", {
    type: "line",
    data: {
      labels: ["Wk 1", "Wk 2", "Wk 3", "Wk 4", "Wk 5", "Wk 6"],
      datasets: [
        { label: "Shipments", data: [62, 70, 58, 84, 92, 75], borderColor: "#2DD4BF", backgroundColor: "rgba(45,212,191,0.18)", fill: true, tension: 0.35 },
        { label: "Avg Risk (%)", data: [38, 41, 36, 47, 52, 44], borderColor: "#F59E0B", backgroundColor: "rgba(245,158,11,0.12)", fill: false, tension: 0.35 }
      ]
    },
    options: { ...common }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.querySelector("canvas[data-pace-chart]")) paceCharts();
});

