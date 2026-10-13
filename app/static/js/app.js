// ==========================================================================
// HustlePulse AI - Interactive Application Logic
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initListingEngine();
  initPricingEngine();
  initVoiceStudio();
  loadSampleDatasets();
});

// Toast notification helper
function showToast(message, isSuccess = true) {
  const toast = document.getElementById("toast-notification");
  if (!toast) return;
  toast.innerHTML = `<span>${isSuccess ? '✅' : 'ℹ️'}</span> <span>${message}</span>`;
  toast.classList.add("show");
  setTimeout(() => {
    toast.classList.remove("show");
  }, 3500);
}

// --------------------------------------------------------------------------
// Navigation & Tab Switching
// --------------------------------------------------------------------------
function initTabs() {
  const tabButtons = document.querySelectorAll(".nav-tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");

  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");

      tabButtons.forEach(b => b.classList.remove("active"));
      tabContents.forEach(c => c.classList.remove("active"));

      btn.classList.add("active");
      const activeContent = document.getElementById(`tab-${targetTab}`);
      if (activeContent) activeContent.classList.add("active");
    });
  });
}

// --------------------------------------------------------------------------
// Module 1: Gemma Listing & SEO Generator
// --------------------------------------------------------------------------
const LISTING_PRESETS = {
  candles: {
    title: "Hand-Poured Amber & Oakmoss Soy Candle 8oz",
    category: "Home & Living / Candles",
    materials: "100% American Soy Wax, Premium Phthalate-Free Fragrance, Crackling Wooden Wick, Amber Glass Tumbler",
    features: "50-hour clean burn, artisanal small batch, notes of oakmoss, amber, and vetiver, reusable jar",
    target_audience: "Cozy home decor enthusiasts and lovers of warm, earthy botanical scents",
    tone: "Artisan & Authentic",
    platform: "Etsy"
  },
  leather: {
    title: "Slim Horween Chromexcel Bifold Leather Wallet",
    category: "Accessories / Wallets",
    materials: "Full-Grain Horween Chromexcel Leather, Waxed Poly Thread, Hand-Beveled & Burnished Edges",
    features: "Holds 8-10 cards plus folded cash, minimalist profile, develops rich patina over time, lifetime guarantee",
    target_audience: "Minimalist everyday carry (EDC) enthusiasts and heritage leather connoisseurs",
    tone: "Luxury & Minimalist",
    platform: "Shopify"
  },
  digital: {
    title: "Second Brain & Solopreneur Client Hub Notion Template",
    category: "Digital Products / Productivity",
    materials: "Interactive Notion Workspace, 14 Linked Databases, Video Walkthrough Guide, Mobile Layout",
    features: "Automated project tracking, client CRM, invoice generator, quick-capture dashboard",
    target_audience: "Freelancers, agency founders, and indie creators scaling their business",
    tone: "Punchy & Direct",
    platform: "Gumroad / Etsy"
  }
};

function initListingEngine() {
  const form = document.getElementById("listing-generator-form");
  const presetChips = document.querySelectorAll(".listing-preset-chip");
  const submitBtn = document.getElementById("btn-generate-listing");

  // Preset chip clicks
  presetChips.forEach(chip => {
    chip.addEventListener("click", () => {
      presetChips.forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      const key = chip.getAttribute("data-preset");
      const data = LISTING_PRESETS[key];
      if (data) {
        document.getElementById("item-title").value = data.title;
        document.getElementById("item-category").value = data.category;
        document.getElementById("item-materials").value = data.materials;
        document.getElementById("item-features").value = data.features;
        document.getElementById("item-audience").value = data.target_audience;
        document.getElementById("item-tone").value = data.tone;
        document.getElementById("item-platform").value = data.platform;
      }
    });
  });

  // Submit Handler
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span class="spinner"></span> Generating with Gemma...`;

    const payload = {
      title: document.getElementById("item-title").value,
      category: document.getElementById("item-category").value,
      materials: document.getElementById("item-materials").value,
      features: document.getElementById("item-features").value,
      target_audience: document.getElementById("item-audience").value,
      tone: document.getElementById("item-tone").value,
      platform: document.getElementById("item-platform").value
    };

    try {
      const res = await fetch("/api/generate-listing", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      renderListingOutput(data);
      showToast("Listing generated with open-weight Gemma!");
    } catch (err) {
      console.error(err);
      showToast("Failed to generate listing. Check console.", false);
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `<span>✨ Generate High-Converting Listing</span>`;
    }
  });

  // Copy buttons
  document.querySelectorAll(".copy-trigger").forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-target");
      const targetElem = document.getElementById(targetId);
      if (targetElem) {
        navigator.clipboard.writeText(targetElem.innerText || targetElem.value);
        showToast("Copied to clipboard!");
      }
    });
  });
}

function renderListingOutput(data) {
  document.getElementById("output-optimized-title").innerText = data.optimized_title || "";
  document.getElementById("output-hook").innerText = data.hook || "";
  document.getElementById("output-description").innerText = data.description || "";
  document.getElementById("output-buyer-persona").innerText = data.buyer_persona || "";
  document.getElementById("output-video-hook").innerText = data.social_video_hook || "";

  // Set script into Voice tab automatically
  const voiceScriptInput = document.getElementById("voice-script-input");
  if (voiceScriptInput && data.social_video_hook) {
    voiceScriptInput.value = `${data.social_video_hook} ${data.hook}`;
  }

  // Render Bullets
  const bulletsContainer = document.getElementById("output-bullets");
  bulletsContainer.innerHTML = "";
  if (data.bullet_points && Array.isArray(data.bullet_points)) {
    data.bullet_points.forEach(bp => {
      const li = document.createElement("li");
      li.style.marginBottom = "0.4rem";
      li.innerText = bp;
      bulletsContainer.appendChild(li);
    });
  }

  // Render SEO Tags
  const tagsContainer = document.getElementById("output-tags-cloud");
  tagsContainer.innerHTML = "";
  if (data.seo_tags && Array.isArray(data.seo_tags)) {
    data.seo_tags.forEach(tag => {
      const span = document.createElement("span");
      span.className = "tag-item";
      span.innerText = tag;
      tagsContainer.appendChild(span);
    });
  }

  // Engine metadata badge
  if (data._meta) {
    document.getElementById("gemma-meta-info").innerText = 
      `Engine: ${data._meta.engine} | Latency: ${data._meta.latency_ms}ms | Cost: ${data._meta.cost}`;
  }

  document.getElementById("listing-output-section").scrollIntoView({ behavior: "smooth" });
}

// --------------------------------------------------------------------------
// Module 2: TabPFN Dynamic Pricing & Elasticity Engine
// --------------------------------------------------------------------------
let sampleDatasetsCache = {};
let customUploadedCsv = null;

async function loadSampleDatasets() {
  try {
    const res = await fetch("/api/sample-datasets");
    sampleDatasetsCache = await res.json();
    populateDatasetSelector();
  } catch (e) {
    console.error("Failed to load sample datasets", e);
  }
}

function populateDatasetSelector() {
  const selector = document.getElementById("pricing-dataset-select");
  if (!selector) return;
  selector.innerHTML = `
    <option value="candles">🕯️ Handcrafted Soy Candles (20 records)</option>
    <option value="leather">👝 Custom Leathercraft Goods (12 records)</option>
    <option value="digital">💻 Digital Notion Templates (10 records)</option>
    <option value="custom">📁 Custom CSV Upload...</option>
  `;
}

function initPricingEngine() {
  const form = document.getElementById("pricing-predict-form");
  const datasetSelect = document.getElementById("pricing-dataset-select");
  const uploadInput = document.getElementById("csv-file-upload");
  const submitBtn = document.getElementById("btn-predict-pricing");

  datasetSelect.addEventListener("change", () => {
    const key = datasetSelect.value;
    if (key === "custom") {
      document.getElementById("custom-upload-group").style.display = "block";
    } else {
      document.getElementById("custom-upload-group").style.display = "none";
      const ds = sampleDatasetsCache[key];
      if (ds && ds.default_candidate) {
        document.getElementById("price-material-cost").value = ds.default_candidate.material_cost || ds.default_candidate.creation_hours || 5.0;
        document.getElementById("price-labor-hours").value = ds.default_candidate.labor_hours || 0.6;
        document.getElementById("price-competitor-price").value = ds.default_candidate.competitor_avg_price || 25.0;
        document.getElementById("price-photo-count").value = ds.default_candidate.photo_count || 6;
      }
    }
  });

  // CSV upload handler
  uploadInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/upload-csv", { method: "POST", body: formData });
      const data = await res.json();
      customUploadedCsv = data.raw_csv;
      showToast(`Uploaded ${data.filename} (${data.row_count} rows)`);
    } catch (err) {
      console.error(err);
      showToast("CSV parsing error", false);
    }
  });

  // Submit Handler
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span class="spinner"></span> TabPFN Forecasting...`;

    const datasetType = datasetSelect.value;
    const candidate = {
      material_cost: parseFloat(document.getElementById("price-material-cost").value || "5.0"),
      labor_hours: parseFloat(document.getElementById("price-labor-hours").value || "0.5"),
      competitor_avg_price: parseFloat(document.getElementById("price-competitor-price").value || "25.0"),
      photo_count: parseInt(document.getElementById("price-photo-count").value || "6"),
      is_q4_holiday: parseInt(document.getElementById("price-season-q4").value || "1"),
      free_shipping: parseInt(document.getElementById("price-free-shipping").value || "1")
    };

    const payload = {
      dataset_type: datasetType,
      custom_csv_data: (datasetType === "custom") ? customUploadedCsv : null,
      candidate_item: candidate,
      target_column: "final_price"
    };

    try {
      const res = await fetch("/api/predict-pricing", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      renderPricingOutput(data);
      showToast("TabPFN pricing prediction complete!");
    } catch (err) {
      console.error(err);
      showToast("Prediction error", false);
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `<span>📊 Predict Optimal Price with TabPFN</span>`;
    }
  });
}

function renderPricingOutput(data) {
  document.getElementById("metric-optimal-price").innerText = `$${data.optimal_recommended_price.toFixed(2)}`;
  document.getElementById("metric-units-sold").innerText = `${data.estimated_units_sold} units/mo`;
  document.getElementById("metric-revenue").innerText = `$${data.projected_monthly_revenue.toFixed(2)}`;
  document.getElementById("metric-margin").innerText = `${data.profit_margin_percent}% margin ($${data.projected_monthly_profit.toFixed(2)})`;

  // Model Engine Info
  if (data._meta) {
    document.getElementById("tabpfn-meta-info").innerText = 
      `Engine: ${data._meta.model_engine} | Latency: ${data._meta.latency_ms}ms | Training: ${data.training_samples_count} rows`;
    if (data._meta.note) {
      document.getElementById("tabpfn-note-banner").innerText = data._meta.note;
      document.getElementById("tabpfn-note-banner").style.display = "block";
    }
  }

  // Elasticity Table
  const tbody = document.getElementById("elasticity-table-body");
  tbody.innerHTML = "";
  if (data.elasticity_curve) {
    data.elasticity_curve.forEach(row => {
      const tr = document.createElement("tr");
      if (row.is_recommended) tr.className = "recommended-row";
      tr.innerHTML = `
        <td><strong>$${row.price.toFixed(2)}</strong> ${row.is_recommended ? '<span class="badge pulse-emerald">Recommended</span>' : ''}</td>
        <td>${row.multiplier}</td>
        <td>${row.predicted_units} units</td>
        <td>$${row.projected_revenue.toFixed(2)}</td>
        <td style="color: ${row.projected_profit > 0 ? '#34d399' : '#f43f5e'}">$${row.projected_profit.toFixed(2)}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  // Anomalies List
  const anomalyContainer = document.getElementById("anomalies-list-container");
  anomalyContainer.innerHTML = "";
  if (data.historical_anomalies && data.historical_anomalies.length > 0) {
    data.historical_anomalies.forEach(a => {
      const item = document.createElement("div");
      item.style.padding = "0.6rem 0";
      item.style.borderBottom = "1px solid rgba(255,255,255,0.05)";
      item.style.display = "flex";
      item.style.justifyContent = "space-between";
      item.style.fontSize = "0.85rem";
      item.innerHTML = `
        <div>
          <strong>${a.item_name}</strong>
          <div style="color: var(--text-dim); font-size: 0.78rem;">Price: ${a.current_price} | Cost: ${a.estimated_cost}</div>
        </div>
        <div style="text-align: right;">
          <span class="badge pulse-amber">${a.status}</span>
          <div style="color: var(--text-muted); font-size: 0.78rem;">Margin: ${a.margin_percent}</div>
        </div>
      `;
      anomalyContainer.appendChild(item);
    });
  } else {
    anomalyContainer.innerHTML = `<p style="color: var(--text-muted); font-size: 0.85rem;">No margin anomalies detected in dataset. Your listings are well-priced!</p>`;
  }

  document.getElementById("pricing-output-section").scrollIntoView({ behavior: "smooth" });
}

// --------------------------------------------------------------------------
// Module 3: ElevenLabs Audio Promo Studio
// --------------------------------------------------------------------------
let activeAudio = null;

function initVoiceStudio() {
  const form = document.getElementById("voice-studio-form");
  const submitBtn = document.getElementById("btn-generate-voice");
  const playBtn = document.getElementById("btn-play-audio");
  const downloadBtn = document.getElementById("btn-download-audio");
  const waveBars = document.querySelectorAll(".wave-bar");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span class="spinner"></span> Synthesizing Voice...`;

    const script = document.getElementById("voice-script-input").value;
    const preset = document.getElementById("voice-preset-select").value;

    try {
      const res = await fetch("/api/generate-voice", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ script_text: script, voice_preset: preset })
      });
      const data = await res.json();
      renderVoiceOutput(data, script);
      showToast("Voice narration generated!");
    } catch (err) {
      console.error(err);
      showToast("Voice generation error", false);
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `<span>🎙️ Generate High-Definition Promo Voice</span>`;
    }
  });

  // Play button handler
  playBtn.addEventListener("click", () => {
    if (activeAudio) {
      if (activeAudio.paused) {
        activeAudio.play();
        setWaveformActive(true);
        playBtn.innerText = "⏸️ Pause Audio";
      } else {
        activeAudio.pause();
        setWaveformActive(false);
        playBtn.innerText = "▶️ Play Narration";
      }
    } else {
      // Browser Speech Synthesis fallback
      const script = document.getElementById("voice-script-input").value;
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(script);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        setWaveformActive(true);
        utterance.onend = () => {
          setWaveformActive(false);
          playBtn.innerText = "▶️ Play Narration";
        };
        window.speechSynthesis.speak(utterance);
        playBtn.innerText = "⏸️ Playing (Web Speech)...";
      } else {
        showToast("Speech synthesis not supported in this browser.", false);
      }
    }
  });

  function setWaveformActive(isActive) {
    waveBars.forEach(b => {
      if (isActive) b.classList.add("playing");
      else b.classList.remove("playing");
    });
  }
}

function renderVoiceOutput(data, rawScript) {
  const playerBox = document.getElementById("audio-player-container");
  const playBtn = document.getElementById("btn-play-audio");
  const downloadBtn = document.getElementById("btn-download-audio");
  const metaSpan = document.getElementById("voice-meta-info");

  playerBox.style.display = "block";
  metaSpan.innerText = `Voice: ${data.voice_name} | Engine: ${data.engine} (${data.latency_ms}ms)`;

  if (data.audio_base64) {
    activeAudio = new Audio(data.audio_base64);
    downloadBtn.style.display = "inline-flex";
    downloadBtn.onclick = () => {
      const a = document.createElement("a");
      a.href = data.audio_base64;
      a.download = "hustlepulse_promo_voice.mp3";
      a.click();
    };
  } else {
    activeAudio = null;
    downloadBtn.style.display = "none";
  }

  playBtn.innerText = "▶️ Play Narration";
}
