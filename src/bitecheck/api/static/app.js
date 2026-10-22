/**
 * BiteCheck India — Interactive SPA Frontend Logic (Phase 9)
 * Manages preset product audits, image uploads, SVG score gauge animation,
 * and live multi-agent result rendering.
 */

const PRESETS = {
  cookie: {
    brand_name: "GoodBite",
    product_name: "Diet Oats Biscuit",
    front_claims: ["Rich in Oats", "Zero Added Sugar", "Healthy Choice"],
    ingredients_raw: ["Refined Wheat Flour (Maida) 55%", "Palm Oil", "Maltodextrin", "Oats 4%", "Salt"],
    net_weight_g: 100.0,
    serving_size_g: 20.0,
    nutrition_per_100g: {
      energy_kcal: 450.0,
      fat_g: 18.0,
      saturated_fat_g: 8.0,
      trans_fat_g: 0.0,
      carbohydrates_g: 68.0,
      dietary_fiber_g: 2.0,
      sugar_g: 1.0,
      added_sugar_g: 0.0,
      sodium_mg: 550.0,
      protein_g: 5.0,
    },
    fssai_license_number: "10012011000123",
    dietary_dot: "GREEN_VEG",
  },
  namkeen: {
    brand_name: "CrunchTime",
    product_name: "Lite Multigrain Namkeen",
    front_claims: ["Baked Not Fried", "Cholesterol Free", "Heart Friendly"],
    ingredients_raw: ["Palmolein Oil 32%", "Corn Flour", "Refined Flour", "Salt", "Spices", "INS 621"],
    net_weight_g: 150.0,
    serving_size_g: 30.0,
    nutrition_per_100g: {
      energy_kcal: 520.0,
      fat_g: 32.0,
      saturated_fat_g: 15.0,
      trans_fat_g: 0.0,
      carbohydrates_g: 54.0,
      dietary_fiber_g: 1.5,
      sugar_g: 2.0,
      added_sugar_g: 0.0,
      sodium_mg: 1200.0,
      protein_g: 6.0,
    },
    fssai_license_number: "10019011004567",
    dietary_dot: "GREEN_VEG",
  },
  oats: {
    brand_name: "True Elements",
    product_name: "Rolled Oats",
    front_claims: ["100% Whole Grain", "High Dietary Fiber", "No Preservatives"],
    ingredients_raw: ["Rolled Oats 100%"],
    net_weight_g: 500.0,
    serving_size_g: 40.0,
    nutrition_per_100g: {
      energy_kcal: 380.0,
      fat_g: 7.0,
      saturated_fat_g: 1.2,
      trans_fat_g: 0.0,
      carbohydrates_g: 65.0,
      dietary_fiber_g: 10.0,
      sugar_g: 0.5,
      added_sugar_g: 0.0,
      sodium_mg: 5.0,
      protein_g: 13.0,
    },
    fssai_license_number: "10019022009876",
    dietary_dot: "GREEN_VEG",
  },
};

function switchTab(tab) {
  const tabPresets = document.getElementById("tab-presets");
  const tabUpload = document.getElementById("tab-upload");
  const contentPresets = document.getElementById("content-presets");
  const contentUpload = document.getElementById("content-upload");

  if (tab === "presets") {
    tabPresets.classList.add("active");
    tabUpload.classList.remove("active");
    contentPresets.classList.remove("hidden");
    contentUpload.classList.add("hidden");
  } else {
    tabUpload.classList.add("active");
    tabPresets.classList.remove("active");
    contentUpload.classList.remove("hidden");
    contentPresets.classList.add("hidden");
  }
}

function showLoading(stepText) {
  const overlay = document.getElementById("loading-overlay");
  const stepLabel = document.getElementById("loading-step");
  if (stepLabel && stepText) stepLabel.innerText = stepText;
  overlay.classList.remove("hidden");
}

function hideLoading() {
  const overlay = document.getElementById("loading-overlay");
  overlay.classList.add("hidden");
}

function previewImage(type, input) {
  if (input.files && input.files[0]) {
    const reader = new FileReader();
    reader.onload = function (e) {
      const preview = document.getElementById(`preview-${type}`);
      const prompt = document.getElementById(`prompt-${type}`);
      preview.src = e.target.result;
      preview.classList.remove("hidden");
      prompt.classList.add("hidden");
    };
    reader.readAsDataURL(input.files[0]);
  }
}

async function runPreset(key) {
  const data = PRESETS[key];
  if (!data) return;

  showLoading(`Dispatching Multi-Agent State Graph for '${data.product_name}'...`);

  try {
    const response = await fetch("/api/audit/json", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`Server returned HTTP ${response.status}`);
    }

    const state = await response.json();
    renderResults(state);
  } catch (err) {
    console.error("Audit request failed:", err);
    alert(`Audit request failed: ${err.message}. Ensure BiteCheck API is running.`);
  } finally {
    hideLoading();
  }
}

async function handleUploadSubmit(e) {
  e.preventDefault();
  const frontFile = document.getElementById("front-file").files[0];
  const backFile = document.getElementById("back-file").files[0];

  if (!frontFile || !backFile) {
    alert("Please select both Front and Back packaging photographs.");
    return;
  }

  showLoading("Agent 1 Ingesting packaging & running Gemini Vision OCR...");

  const formData = new FormData();
  formData.append("front_image", frontFile);
  formData.append("back_image", backFile);

  try {
    const response = await fetch("/api/audit/upload", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Server returned HTTP ${response.status}`);
    }

    const state = await response.json();
    renderResults(state);
  } catch (err) {
    console.error("Upload audit failed:", err);
    alert(`Multimodal upload failed: ${err.message}`);
  } finally {
    hideLoading();
  }
}

function animateGauge(score, colorCode) {
  const circle = document.getElementById("gauge-circle");
  const numberElem = document.getElementById("card-score");
  if (!circle || !numberElem) return;

  const circumference = 314.15; // 2 * pi * 50
  const offset = circumference - (score / 100) * circumference;
  circle.style.strokeDashoffset = offset;

  // Color mapping
  if (colorCode === "GREEN") {
    circle.style.stroke = "var(--color-green)";
  } else if (colorCode === "AMBER") {
    circle.style.stroke = "var(--color-amber)";
  } else {
    circle.style.stroke = "var(--color-red)";
  }

  // Count up animation
  let current = 0;
  const step = Math.max(1, Math.floor(score / 30));
  const interval = setInterval(() => {
    current += step;
    if (current >= score) {
      current = score;
      clearInterval(interval);
    }
    numberElem.innerText = current;
  }, 25);
}

function renderResults(state) {
  const card = state.transparency_card || {};
  const scorecard = state.scorecard || {};
  const reality = card.whole_pack_reality || {};

  document.getElementById("results-dashboard").classList.remove("hidden");

  // 1. Header Information
  document.getElementById("card-brand").innerText = card.brand_name || "Food Brand";
  document.getElementById("card-product").innerText = card.product_name || "Audited Food";
  document.getElementById("card-verdict").innerText = card.verdict_summary || "";

  // Telemetry Latency
  const totalMs = state.execution_times_ms?.parallel_evaluation_wall_time || 0;
  document.getElementById("telemetry-latency").innerText = `${Math.round(totalMs)}ms`;

  // 2. Score Gauge
  const score = card.honesty_score ?? 0;
  const color = card.color_code || "RED";
  animateGauge(score, color);

  const bracketElem = document.getElementById("card-bracket");
  bracketElem.innerText = card.bracket || "UNKNOWN";
  bracketElem.className = `bracket-badge ${color.toLowerCase()}`;

  const overrideAlert = document.getElementById("card-override-alert");
  if (card.critical_override_applied) {
    overrideAlert.classList.remove("hidden");
  } else {
    overrideAlert.classList.add("hidden");
  }

  // 3. Whole Pack Reality Table
  document.getElementById("pill-multiplier").innerText = `${reality.multiplier || 1.0}x Whole Pack`;
  document.getElementById("reality-cal-adv").innerText = `${reality.calories_advertised || 0} kcal`;
  document.getElementById("reality-cal-pack").innerText = `${reality.calories_whole_pack || 0} kcal`;
  document.getElementById("reality-sugar-adv").innerText = `${reality.sugar_advertised_g || 0}g`;
  document.getElementById("reality-sugar-pack").innerText = `${reality.sugar_whole_pack_g || 0}g`;
  document.getElementById("reality-sodium-adv").innerText = `${reality.sodium_advertised_mg || 0}mg`;
  document.getElementById("reality-sodium-pack").innerText = `${reality.sodium_whole_pack_mg || 0}mg`;

  const glycemicAlert = document.getElementById("glycemic-alert");
  if (reality.glycemic_spike_alert) {
    glycemicAlert.classList.remove("hidden");
    document.getElementById("carb-fiber-val").innerText = reality.carb_to_fiber_ratio || 0;
  } else {
    glycemicAlert.classList.add("hidden");
  }

  // 4. Badges Container
  const badgesContainer = document.getElementById("badges-container");
  badgesContainer.innerHTML = "";
  const badges = card.active_badges || [];
  if (badges.length === 0) {
    badgesContainer.innerHTML = '<span class="badge-tag clean-badge">✅ NO REGULATORY VIOLATIONS</span>';
  } else {
    badges.forEach((b) => {
      badgesContainer.innerHTML += `<span class="badge-tag">⚠️ ${b.replace(/_/g, " ")}</span>`;
    });
  }

  // 5. Evidence Chain
  const evidenceList = document.getElementById("evidence-list");
  evidenceList.innerHTML = "";
  const evidence = card.evidence_chain || [];
  if (evidence.length === 0) {
    evidenceList.innerHTML = '<p class="evidence-snippet">Label ingredients strictly adhere to FSSAI standards.</p>';
  } else {
    evidence.forEach((ev) => {
      evidenceList.innerHTML += `
        <div class="evidence-item">
          <div class="evidence-header">
            <span>${ev.badge}</span>
            <span>-${ev.penalty_deduction} pts</span>
          </div>
          <div class="evidence-reason">${ev.scientific_reason}</div>
          <div class="evidence-snippet">Label Proof: "${ev.label_evidence_snippet}"</div>
        </div>
      `;
    });
  }

  // 6. Consumer Sentiment Pulse
  const pulse = card.sentiment_pulse || {};
  document.getElementById("pulse-authenticity").innerText = `${pulse.authenticity_score || 100}% Authentic`;
  document.getElementById("pulse-summary").innerText = pulse.reddit_summary || "Community forums validate label transparency.";

  const distressBox = document.getElementById("distress-box");
  const distressDesc = document.getElementById("distress-desc");
  if (pulse.digestive_distress_alert) {
    distressBox.classList.remove("hidden");
    const effects = pulse.top_side_effects ? pulse.top_side_effects.join(", ") : "bloating, acidity";
    distressDesc.innerText = `Consumers report repeated issues: ${effects}.`;
  } else {
    distressBox.classList.add("hidden");
  }

  // 7. Clean Swaps
  const swapsList = document.getElementById("swaps-list");
  const swapsDesc = document.getElementById("swaps-desc");
  swapsList.innerHTML = "";
  const swaps = card.clean_swaps || [];

  if (card.is_clean_product || swaps.length === 0) {
    swapsDesc.innerText = "This product scored in the Clean & Transparent tier. No brand swap needed!";
    swapsList.innerHTML = '<div class="swap-item"><span class="swap-brand">Verified Clean Label</span><div class="swap-product">Safe for daily consumption</div></div>';
  } else {
    swapsDesc.innerText = "Healthier, 100% whole grain & palm-oil-free alternatives on quick commerce:";
    swaps.forEach((sw) => {
      const platformTags = (sw.platforms || []).map((p) => `<span class="platform-tag">${p}</span>`).join("");
      swapsList.innerHTML += `
        <div class="swap-item">
          <span class="swap-brand">${sw.brand}</span>
          <div class="swap-product">${sw.product}</div>
          <div class="swap-why">${sw.why_clean}</div>
          <div class="swap-platforms">${platformTags}</div>
        </div>
      `;
    });
  }

  // Smooth scroll to results
  document.getElementById("results-dashboard").scrollIntoView({ behavior: "smooth", block: "start" });
}
