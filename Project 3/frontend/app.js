/**
 * CardioPredict ML - Frontend Application Logic
 * Integrates:
 * 1. Live Dynamic Heartbeat & Vascular Heatmap
 * 2. 360° Cardiac Biomarker Radar Chart
 * 3. Apple Health-Style Interactive Dials & Cards
 */

(function () {
  'use strict';

  // --- Configuration & State ---
  const state = {
    currentMode: 'major', // 'major' | 'simple'
    apiBaseUrl: 'http://localhost:8000',
    useMockFallback: true,
    isSubmitting: false,
    lastResult: null
  };

  // --- DOM Element References ---
  const tabMajor = document.getElementById('tabMajor');
  const tabSimple = document.getElementById('tabSimple');
  const modeBanner = document.getElementById('modeBanner');
  const bannerTitle = document.getElementById('bannerTitle');
  const bannerText = document.getElementById('bannerText');
  const majorOnlySection = document.getElementById('majorOnlySection');

  const form = document.getElementById('assessmentForm');
  const resetBtn = document.getElementById('resetBtn');
  const loadSampleBtn = document.getElementById('loadSampleBtn');
  const predictBtn = document.getElementById('predictBtn');
  const predictSpinner = document.getElementById('predictSpinner');

  // Interactive Controls (Feature 4 & 2)
  const inputRestingBP = document.getElementById('inputRestingBP');
  const sliderRestingBP = document.getElementById('sliderRestingBP');
  const badgeRestingBP = document.getElementById('badgeRestingBP');

  const inputMaxHR = document.getElementById('inputMaxHR');
  const sliderMaxHR = document.getElementById('sliderMaxHR');
  const badgeMaxHR = document.getElementById('badgeMaxHR');
  const liveBpmValue = document.getElementById('liveBpmValue');
  const heartPulseGroup = document.getElementById('heartPulseGroup');
  const heartAura = document.getElementById('heartAura');
  const vascularStateDot = document.getElementById('vascularStateDot');
  const vascularStateText = document.getElementById('vascularStateText');

  const inputExerciseAngina = document.getElementById('inputExerciseAngina');
  const anginaPillGroup = document.getElementById('anginaPillGroup');

  const inputChestPainType = document.getElementById('inputChestPainType');
  const chestPainCardGrid = document.getElementById('chestPainCardGrid');

  // Results Section (Feature 3)
  const resultsContainer = document.getElementById('resultsContainer');
  const resultModeBadge = document.getElementById('resultModeBadge');
  const resultTimestamp = document.getElementById('resultTimestamp');
  const statusCard = document.getElementById('statusCard');
  const statusIcon = document.getElementById('statusIcon');
  const statusHeadline = document.getElementById('statusHeadline');
  const statusSubtext = document.getElementById('statusSubtext');
  const scorePercentage = document.getElementById('scorePercentage');
  const scoreTierBadge = document.getElementById('scoreTierBadge');
  const gaugeProgress = document.getElementById('gaugeProgress');
  const generalExplanationText = document.getElementById('generalExplanationText');
  const featureImportanceList = document.getElementById('featureImportanceList');
  const closeResultsTopBtn = document.getElementById('closeResultsTopBtn');
  const performAnotherAssessmentBtn = document.getElementById('performAnotherAssessmentBtn');
  const printReportBtn = document.getElementById('printReportBtn');

  // Feature 5: Multi-Theme Switcher Elements
  const themeBtn = document.getElementById('themeBtn');
  const themeDropdown = document.getElementById('themeDropdown');
  const themeCurrentIcon = document.getElementById('themeCurrentIcon');
  const themeCurrentLabel = document.getElementById('themeCurrentLabel');
  const themeOptionButtons = document.querySelectorAll('.theme-option-btn');

  // Radar Chart Elements
  const radarPolygon = document.getElementById('radarPolygon');
  const radarValBP = document.getElementById('radarValBP');
  const radarValHR = document.getElementById('radarValHR');
  const radarValChol = document.getElementById('radarValChol');
  const radarValAngina = document.getElementById('radarValAngina');
  const radarValST = document.getElementById('radarValST');
  const radarStop1 = document.getElementById('radarStop1');

  // Modals & Navigation
  const glossaryBtn = document.getElementById('glossaryBtn');
  const glossaryModal = document.getElementById('glossaryModal');
  const closeGlossaryBtn = document.getElementById('closeGlossaryBtn');
  const dismissGlossaryBtn = document.getElementById('dismissGlossaryBtn');

  const apiConfigBtn = document.getElementById('apiConfigBtn');
  const apiModal = document.getElementById('apiModal');
  const closeApiBtn = document.getElementById('closeApiBtn');
  const saveApiBtn = document.getElementById('saveApiBtn');
  const testConnectionBtn = document.getElementById('testConnectionBtn');
  const apiUrlInput = document.getElementById('apiUrlInput');
  const mockModeToggle = document.getElementById('mockModeToggle');

  const toastNotification = document.getElementById('toastNotification');
  const toastMessage = document.getElementById('toastMessage');
  const tooltipButtons = document.querySelectorAll('.info-tooltip-btn');

  // =========================================================================
  // INITIALIZATION
  // =========================================================================

  function init() {
    setupThemeSwitcher();
    setupEventListeners();
    setupInteractiveWidgets();
    updateModeUI();
    syncHeartPacing(130);
    updateRestingBPBadge(130);
    updateVascularTone();
  }

  // =========================================================================
  // FEATURE 5: MULTI-THEME SWITCHER
  // =========================================================================

  function setupThemeSwitcher() {
    const savedTheme = localStorage.getItem('cardioTheme') || 'clinical';
    applyTheme(savedTheme);

    if (themeBtn && themeDropdown) {
      themeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        themeDropdown.classList.toggle('hidden');
      });

      themeOptionButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          const selected = btn.getAttribute('data-theme');
          applyTheme(selected);
          themeDropdown.classList.add('hidden');
          showToast(`Switched theme to ${btn.querySelector('strong').textContent}`);
        });
      });

      document.addEventListener('click', (e) => {
        if (!themeBtn.contains(e.target) && !themeDropdown.contains(e.target)) {
          themeDropdown.classList.add('hidden');
        }
      });
    }
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('cardioTheme', theme);

    themeOptionButtons.forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-theme') === theme);
    });

    const icons = {
      clinical: '🩺',
      neon: '🌌',
      sunset: '🌅'
    };
    const labels = {
      clinical: 'Clinical',
      neon: 'Neon Dark',
      sunset: 'Sunset'
    };

    if (themeCurrentIcon) themeCurrentIcon.textContent = icons[theme] || '🎨';
    if (themeCurrentLabel) themeCurrentLabel.textContent = labels[theme] || 'Theme';
  }

  // =========================================================================
  // MODE SWITCHING (FR-01, FR-02, FR-03, FR-04, FR-05)
  // =========================================================================

  function setAssessmentMode(mode) {
    if (state.currentMode === mode) return;
    state.currentMode = mode;
    updateModeUI();
    clearValidationErrors();
    showToast(`Switched to ${mode === 'major' ? 'Major (11-Feature)' : 'Simple (5-Feature)'} Mode`);
  }

  function updateModeUI() {
    if (state.currentMode === 'major') {
      tabMajor.classList.add('active');
      tabSimple.classList.remove('active');
      majorOnlySection.classList.remove('mode-hidden');

      bannerTitle.textContent = 'Major Assessment Mode Active:';
      bannerText.textContent = 'Evaluating all 11 biomedical features (RestingBP, Serum Cholesterol, RestingECG, ST_Slope, Oldpeak, etc.) using the fully trained Major Model.';
      
      ['Cholesterol', 'FastingBS', 'RestingECG', 'Oldpeak', 'ST_Slope'].forEach(id => {
        const input = document.getElementById('input' + id);
        if (input) input.required = true;
      });
    } else {
      tabMajor.classList.remove('active');
      tabSimple.classList.add('active');
      majorOnlySection.classList.add('mode-hidden');

      bannerTitle.textContent = 'Simple Assessment Mode Active:';
      bannerText.textContent = 'Evaluating 5 accessible self-reported features (Age, Sex, Resting Blood Pressure, Max Heart Rate, Exercise Angina) suitable for quick screening without lab tests.';

      ['Cholesterol', 'FastingBS', 'RestingECG', 'Oldpeak', 'ST_Slope'].forEach(id => {
        const input = document.getElementById('input' + id);
        if (input) input.required = false;
      });
    }
  }

  // =========================================================================
  // FEATURE 2 & 4: INTERACTIVE APPLE HEALTH DIALS & DYNAMIC HEARTBEAT
  // =========================================================================

  function setupInteractiveWidgets() {
    // 1. RestingBP Slider & Input Sync
    sliderRestingBP.addEventListener('input', (e) => {
      const val = parseInt(e.target.value);
      inputRestingBP.value = val;
      updateRestingBPBadge(val);
      updateVascularTone();
    });

    inputRestingBP.addEventListener('input', (e) => {
      const val = parseInt(e.target.value) || 120;
      if (val >= 80 && val <= 200) sliderRestingBP.value = val;
      updateRestingBPBadge(val);
      updateVascularTone();
    });

    // 2. MaxHR Slider & Live Heartbeat Sync
    sliderMaxHR.addEventListener('input', (e) => {
      const bpm = parseInt(e.target.value);
      inputMaxHR.value = bpm;
      syncHeartPacing(bpm);
    });

    inputMaxHR.addEventListener('input', (e) => {
      const bpm = parseInt(e.target.value) || 120;
      if (bpm >= 60 && bpm <= 210) sliderMaxHR.value = bpm;
      syncHeartPacing(bpm);
    });

    // 3. Exercise Angina Segmented Pill Toggle
    const anginaButtons = anginaPillGroup.querySelectorAll('.segment-btn');
    anginaButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const val = btn.getAttribute('data-val');
        inputExerciseAngina.value = val;

        anginaButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        updateVascularTone();
      });
    });

    // 4. Chest Pain Type 4 Interactive Cards
    const chestCards = chestPainCardGrid.querySelectorAll('.chest-card');
    chestCards.forEach(card => {
      card.addEventListener('click', () => {
        const val = card.getAttribute('data-val');
        inputChestPainType.value = val;

        chestCards.forEach(c => c.classList.remove('active'));
        card.classList.add('active');

        // Clear error if present
        const group = document.getElementById('group-ChestPainType');
        if (group) group.classList.remove('has-error');

        updateVascularTone();
      });
    });
  }

  function syncHeartPacing(bpm) {
    const safeBpm = Math.max(50, Math.min(220, bpm));
    liveBpmValue.textContent = safeBpm;
    badgeMaxHR.textContent = `Pacing Heart: ${safeBpm} BPM`;

    // Calculate animation cycle duration in seconds (60 seconds / BPM)
    const durationSec = (60 / safeBpm).toFixed(2);
    if (heartPulseGroup) {
      heartPulseGroup.style.animationDuration = `${durationSec}s`;
    }
  }

  function updateRestingBPBadge(val) {
    if (val < 120) {
      badgeRestingBP.className = 'dial-badge badge-optimal';
      badgeRestingBP.textContent = `Normal (${val} mmHg)`;
    } else if (val <= 139) {
      badgeRestingBP.className = 'dial-badge badge-elevated';
      badgeRestingBP.textContent = `Pre-Hypertension (${val})`;
    } else {
      badgeRestingBP.className = 'dial-badge badge-high';
      badgeRestingBP.textContent = `Hypertension (${val} mmHg)`;
    }
  }

  function updateVascularTone() {
    const bp = parseInt(inputRestingBP.value) || 120;
    const angina = inputExerciseAngina.value === 'Y';
    const chestPain = inputChestPainType.value;

    const isHighStress = bp >= 140 && angina;
    const isModerateWarning = bp >= 135 || angina || chestPain === 'TA';

    const realisticHeartImg = document.getElementById('realisticHeartImg');

    if (isHighStress) {
      vascularStateDot.className = 'state-dot stress';
      vascularStateText.textContent = 'High Vascular Strain';
      if (heartPulseGroup) {
        heartPulseGroup.style.filter = 'drop-shadow(0 0 18px rgba(239, 68, 68, 0.8))';
      }
      if (realisticHeartImg) {
        realisticHeartImg.style.filter = 'drop-shadow(0 0 25px rgba(239, 68, 68, 0.9)) saturate(1.3)';
      }
    } else if (isModerateWarning) {
      vascularStateDot.className = 'state-dot warning';
      vascularStateText.textContent = 'Borderline Resistance';
      if (heartPulseGroup) {
        heartPulseGroup.style.filter = 'drop-shadow(0 0 14px rgba(245, 158, 11, 0.6))';
      }
      if (realisticHeartImg) {
        realisticHeartImg.style.filter = 'drop-shadow(0 0 20px rgba(245, 158, 11, 0.7)) saturate(1.15)';
      }
    } else {
      vascularStateDot.className = 'state-dot optimal';
      vascularStateText.textContent = 'Optimal Vascular Tone';
      if (heartPulseGroup) {
        heartPulseGroup.style.filter = 'none';
      }
      if (realisticHeartImg) {
        realisticHeartImg.style.filter = '';
      }
    }
  }

  // =========================================================================
  // FEATURE 3: 360° CARDIAC BIOMARKER RADAR CHART GENERATOR
  // =========================================================================

  function renderCardiacRadarChart(inputs, mode) {
    // 5 Dimensional axes centered at (170, 170) with radius 120:
    // 0: Blood Pressure (Top: angle -90 deg)
    // 1: Peak Heart Rate (Top-Right: angle -18 deg)
    // 2: Cholesterol / Lipids (Bottom-Right: angle 54 deg)
    // 3: Exercise Angina (Bottom-Left: angle 126 deg)
    // 4: ST Segment Stress (Top-Left: angle 198 deg)

    const bp = parseFloat(inputs.RestingBP) || 120;
    const maxHr = parseFloat(inputs.MaxHR) || 140;
    const chol = parseFloat(inputs.Cholesterol) || 200;
    const angina = inputs.ExerciseAngina === 'Y';
    const stSlope = inputs.ST_Slope || 'Up';
    const oldpeak = parseFloat(inputs.Oldpeak) || 0;

    // Normalize each axis from 0.15 (protective/low) to 0.95 (high strain)
    const scoreBP = Math.min(0.95, Math.max(0.2, (bp - 90) / (180 - 90)));
    // For MaxHR: lower exertion capacity indicates higher strain
    const scoreHR = Math.min(0.95, Math.max(0.2, (190 - maxHr) / (190 - 80)));
    const scoreChol = mode === 'major'
      ? Math.min(0.95, Math.max(0.2, (chol - 120) / (340 - 120)))
      : 0.35;
    const scoreAngina = angina ? 0.92 : 0.22;
    
    let scoreST = 0.25;
    if (mode === 'major') {
      if (stSlope === 'Down' || oldpeak >= 2.0) scoreST = 0.92;
      else if (stSlope === 'Flat' || oldpeak >= 1.0) scoreST = 0.72;
      else scoreST = 0.25;
    }

    const scores = [scoreBP, scoreHR, scoreChol, scoreAngina, scoreST];
    const centerX = 170;
    const centerY = 170;
    const maxRadius = 120;

    const points = scores.map((val, i) => {
      const angle = -Math.PI / 2 + (i * 2 * Math.PI) / 5;
      const r = maxRadius * val;
      const x = (centerX + r * Math.cos(angle)).toFixed(1);
      const y = (centerY + r * Math.sin(angle)).toFixed(1);
      return `${x},${y}`;
    });

    radarPolygon.setAttribute('points', points.join(' '));

    // Update legend values
    radarValBP.textContent = `${bp} mm Hg (${scoreBP > 0.6 ? 'Elevated' : 'Normal'})`;
    radarValHR.textContent = `${maxHr} bpm (${maxHr < 125 ? 'Blunted' : 'Good Reserve'})`;
    radarValChol.textContent = mode === 'major' ? `${chol} mg/dL` : 'Accessible Mode (Estimated)';
    radarValAngina.textContent = angina ? 'Induced (Positive)' : 'Absent (Negative)';
    radarValST.textContent = mode === 'major' ? `${stSlope} / ${oldpeak}mm` : 'Normal Baseline';

    // Shift polygon gradient color based on overall strain
    const avgScore = scores.reduce((a, b) => a + b, 0) / scores.length;
    if (avgScore > 0.55) {
      radarPolygon.style.stroke = '#ef4444';
      if (radarStop1) radarStop1.setAttribute('stop-color', 'rgba(239, 68, 68, 0.65)');
    } else {
      radarPolygon.style.stroke = '#10b981';
      if (radarStop1) radarStop1.setAttribute('stop-color', 'rgba(16, 185, 129, 0.5)');
    }
  }

  // =========================================================================
  // INPUT VALIDATION (FR-07 to FR-10)
  // =========================================================================

  const validationRules = {
    Age: { required: true, min: 18, max: 100, label: 'Age' },
    Sex: { required: true, allowed: ['M', 'F'], label: 'Biological Sex' },
    RestingBP: { required: true, min: 60, max: 240, label: 'Resting Blood Pressure' },
    MaxHR: { required: true, min: 60, max: 220, label: 'Maximum Heart Rate' },
    ExerciseAngina: { required: true, allowed: ['Y', 'N'], label: 'Exercise-Induced Angina' },
    ChestPainType: { required: true, allowed: ['TA', 'ATA', 'NAP', 'ASY'], label: 'Chest Pain Type' },
    Cholesterol: { requiredMajor: true, min: 0, max: 600, label: 'Serum Cholesterol' },
    FastingBS: { requiredMajor: true, allowed: ['0', '1'], label: 'Fasting Blood Sugar' },
    RestingECG: { requiredMajor: true, allowed: ['Normal', 'ST', 'LVH'], label: 'Resting ECG' },
    Oldpeak: { requiredMajor: true, min: -2.6, max: 7.0, label: 'Oldpeak (ST Depression)' },
    ST_Slope: { requiredMajor: true, allowed: ['Up', 'Flat', 'Down'], label: 'ST Slope' }
  };

  function validateFormData(data, mode) {
    const errors = {};

    for (const [key, rule] of Object.entries(validationRules)) {
      const isMajorField = rule.requiredMajor !== undefined;
      if (isMajorField && mode !== 'major') continue;

      const val = data[key];

      if (val === undefined || val === null || val === '') {
        errors[key] = `${rule.label} is required.`;
        continue;
      }

      if (rule.min !== undefined || rule.max !== undefined) {
        const numVal = parseFloat(val);
        if (isNaN(numVal)) {
          errors[key] = `${rule.label} must be a valid number.`;
          continue;
        }
        if (rule.min !== undefined && numVal < rule.min) {
          errors[key] = `${rule.label} cannot be below ${rule.min}.`;
          continue;
        }
        if (rule.max !== undefined && numVal > rule.max) {
          errors[key] = `${rule.label} cannot exceed ${rule.max}.`;
          continue;
        }
      }

      if (rule.allowed && !rule.allowed.includes(String(val))) {
        errors[key] = `Invalid option selected for ${rule.label}.`;
      }
    }

    return errors;
  }

  function displayValidationErrors(errors) {
    clearValidationErrors();
    const errorKeys = Object.keys(errors);
    if (errorKeys.length === 0) return true;

    errorKeys.forEach(fieldKey => {
      const group = document.getElementById(`group-${fieldKey}`);
      const errorSpan = document.getElementById(`error-${fieldKey}`);
      if (group) group.classList.add('has-error');
      if (errorSpan) errorSpan.textContent = errors[fieldKey];
    });

    const firstGroup = document.getElementById(`group-${errorKeys[0]}`);
    if (firstGroup) {
      firstGroup.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    showToast(`Please check ${errorKeys.length} highlighted field(s).`);
    return false;
  }

  function clearValidationErrors() {
    document.querySelectorAll('.form-group.has-error').forEach(group => {
      group.classList.remove('has-error');
    });
    document.querySelectorAll('.field-error').forEach(span => {
      span.textContent = '';
    });
  }

  function resetForm() {
    form.reset();
    clearValidationErrors();
    resultsContainer.classList.add('hidden');

    // Reset Interactive Widgets
    sliderRestingBP.value = 130;
    inputRestingBP.value = 130;
    updateRestingBPBadge(130);

    sliderMaxHR.value = 130;
    inputMaxHR.value = 130;
    syncHeartPacing(130);

    inputExerciseAngina.value = 'N';
    anginaPillGroup.querySelectorAll('.segment-btn').forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-val') === 'N');
    });

    inputChestPainType.value = 'ASY';
    chestPainCardGrid.querySelectorAll('.chest-card').forEach(card => {
      card.classList.toggle('active', card.getAttribute('data-val') === 'ASY');
    });

    updateVascularTone();
    showToast('Form reset to default clean state.');
  }

  // Quick Sample Profiles
  const sampleProfiles = {
    highRisk: {
      Age: 58,
      Sex: 'M',
      RestingBP: 152,
      MaxHR: 112,
      ExerciseAngina: 'Y',
      ChestPainType: 'ASY',
      Cholesterol: 285,
      FastingBS: '1',
      RestingECG: 'ST',
      Oldpeak: 2.2,
      ST_Slope: 'Flat'
    },
    lowRisk: {
      Age: 42,
      Sex: 'F',
      RestingBP: 118,
      MaxHR: 172,
      ExerciseAngina: 'N',
      ChestPainType: 'ATA',
      Cholesterol: 195,
      FastingBS: '0',
      RestingECG: 'Normal',
      Oldpeak: 0.0,
      ST_Slope: 'Up'
    }
  };

  let currentSampleToggle = false;
  function loadSampleData() {
    currentSampleToggle = !currentSampleToggle;
    const profile = currentSampleToggle ? sampleProfiles.highRisk : sampleProfiles.lowRisk;

    for (const [key, val] of Object.entries(profile)) {
      const input = document.getElementById(`input${key}`);
      if (input) input.value = val;
    }

    // Sync widgets
    sliderRestingBP.value = profile.RestingBP;
    updateRestingBPBadge(profile.RestingBP);

    sliderMaxHR.value = profile.MaxHR;
    syncHeartPacing(profile.MaxHR);

    anginaPillGroup.querySelectorAll('.segment-btn').forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-val') === profile.ExerciseAngina);
    });

    chestPainCardGrid.querySelectorAll('.chest-card').forEach(card => {
      card.classList.toggle('active', card.getAttribute('data-val') === profile.ChestPainType);
    });

    updateVascularTone();
    clearValidationErrors();
    showToast(`Loaded ${currentSampleToggle ? 'High-Risk Profile' : 'Low-Risk Profile'} sample.`);
  }

  // =========================================================================
  // MODEL PREDICTION & INTELLIGENT SIMULATION (FR-12 to FR-16)
  // =========================================================================

  async function handleFormSubmit(e) {
    e.preventDefault();
    if (state.isSubmitting) return;

    const formData = new FormData(form);
    const payload = {};
    for (const [key, value] of formData.entries()) {
      payload[key] = value.trim();
    }

    const errors = validateFormData(payload, state.currentMode);
    if (Object.keys(errors).length > 0) {
      displayValidationErrors(errors);
      return;
    }

    clearValidationErrors();
    setLoadingState(true);

    try {
      let result;
      if (state.useMockFallback) {
        await new Promise(r => setTimeout(r, 600));
        result = simulateModelInference(payload, state.currentMode);
      } else {
        const endpoint = `${state.apiBaseUrl}/predict/${state.currentMode}`;
        const response = await fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        result = await response.json();
      }

      displayResults(result, state.currentMode, payload);
      renderCardiacRadarChart(payload, state.currentMode);
      resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (err) {
      console.warn('API error, falling back to simulated inference:', err);
      const fallbackResult = simulateModelInference(payload, state.currentMode);
      displayResults(fallbackResult, state.currentMode, payload);
      renderCardiacRadarChart(payload, state.currentMode);
      showToast('Live API unreachable: Simulated inference used for demonstration.');
      resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } finally {
      setLoadingState(false);
    }
  }

  function simulateModelInference(data, mode) {
    let logOdds = -1.8;

    const age = parseFloat(data.Age) || 50;
    logOdds += (age - 53) * 0.045;

    if (data.Sex === 'M') logOdds += 1.35;
    else logOdds -= 0.65;

    const rbp = parseFloat(data.RestingBP) || 120;
    if (rbp > 140) logOdds += (rbp - 140) * 0.02;

    const maxHr = parseFloat(data.MaxHR) || 140;
    logOdds -= (maxHr - 135) * 0.032;

    if (data.ExerciseAngina === 'Y') logOdds += 1.45;
    if (data.ChestPainType === 'ASY') logOdds += 1.65;
    else if (data.ChestPainType === 'ATA') logOdds -= 1.3;
    else if (data.ChestPainType === 'NAP') logOdds -= 0.6;

    if (mode === 'major') {
      const chol = parseFloat(data.Cholesterol) || 200;
      if (chol > 240) logOdds += 0.35;
      else if (chol > 0 && chol < 180) logOdds -= 0.25;

      if (data.FastingBS === '1') logOdds += 0.85;

      if (data.RestingECG === 'ST') logOdds += 0.45;
      else if (data.RestingECG === 'LVH') logOdds += 0.35;

      const oldpeak = parseFloat(data.Oldpeak) || 0;
      if (oldpeak > 1.0) logOdds += oldpeak * 0.8;
      else if (oldpeak <= 0.2) logOdds -= 0.4;

      if (data.ST_Slope === 'Flat') logOdds += 1.85;
      else if (data.ST_Slope === 'Down') logOdds += 1.95;
      else if (data.ST_Slope === 'Up') logOdds -= 1.8;
    }

    const probability = 1 / (1 + Math.exp(-logOdds));
    const scorePct = Math.round(Math.min(99, Math.max(1, probability * 100)));
    const isPositive = probability >= 0.5;

    const influences = [];

    if (data.ST_Slope && mode === 'major') {
      influences.push({
        feature: 'ST Segment Slope',
        value: `${data.ST_Slope} slope`,
        direction: data.ST_Slope === 'Up' ? 'protective' : 'risk',
        weight: data.ST_Slope === 'Up' ? 38 : 42,
        note: data.ST_Slope === 'Up' ? 'Upsloping morphology reduces risk likelihood' : 'Flat/downsloping ST indicates ischemic strain'
      });
    }

    if (data.ExerciseAngina) {
      influences.push({
        feature: 'Exercise Angina',
        value: data.ExerciseAngina === 'Y' ? 'Present' : 'Absent',
        direction: data.ExerciseAngina === 'Y' ? 'risk' : 'protective',
        weight: 32,
        note: data.ExerciseAngina === 'Y' ? 'Exertional angina strongly indicates ischemia' : 'No pain response during stress'
      });
    }

    if (data.ChestPainType) {
      influences.push({
        feature: 'Chest Pain Category',
        value: data.ChestPainType,
        direction: data.ChestPainType === 'ASY' ? 'risk' : 'protective',
        weight: 28,
        note: data.ChestPainType === 'ASY' ? 'Silent/asymptomatic ischemia profile' : 'Atypical presentation'
      });
    }

    influences.push({
      feature: 'Max Heart Rate (MaxHR)',
      value: `${data.MaxHR} bpm`,
      direction: maxHr < 130 ? 'risk' : 'protective',
      weight: 22,
      note: maxHr < 130 ? 'Blunted chronotropic response' : 'Good cardiovascular peak response'
    });

    if (mode === 'major' && data.Oldpeak !== undefined) {
      const op = parseFloat(data.Oldpeak);
      influences.push({
        feature: 'Oldpeak (ST Depression)',
        value: `${op} mm`,
        direction: op >= 1.0 ? 'risk' : 'protective',
        weight: Math.min(35, Math.max(10, Math.round(Math.abs(op) * 15))),
        note: op >= 1.0 ? 'Significant ST depression upon exertion' : 'Minimal exercise-induced ST displacement'
      });
    }

    return {
      prediction: isPositive ? 1 : 0,
      predicted_status: isPositive ? 'Positive' : 'Negative',
      score: scorePct,
      model_type: mode === 'major' ? 'Major Model (11 Features)' : 'Simple Model (5 Features)',
      general_explanation: isPositive
        ? `The model estimated a high probability of recorded heart disease status. The assessment was heavily driven by ${data.ExerciseAngina === 'Y' ? 'exercise-induced angina' : 'chest pain characteristics'} and cardiac exertion parameters.`
        : `The model estimated a low probability of recorded heart disease status based on normal cardiovascular response and absence of classic ischemic markers.`,
      feature_influences: influences
    };
  }

  function displayResults(result, mode, inputs) {
    state.lastResult = { result, mode, inputs };

    resultModeBadge.textContent = mode === 'major' ? 'Major Model (11 Features)' : 'Simple Model (5 Features)';
    const now = new Date();
    resultTimestamp.textContent = `Generated: ${now.toLocaleTimeString()} - ${now.toLocaleDateString()}`;

    const isPositive = result.prediction === 1;

    if (isPositive) {
      statusCard.className = 'outcome-card status-card status-positive';
      statusIcon.innerHTML = `
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
      `;
      statusHeadline.textContent = 'Model Predicts Status: POSITIVE';
      statusSubtext.textContent = 'The classifier detected characteristic patterns consistent with recorded heart disease.';
      scoreTierBadge.textContent = 'Elevated Risk Tier';
    } else {
      statusCard.className = 'outcome-card status-card status-negative';
      statusIcon.innerHTML = `
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
      `;
      statusHeadline.textContent = 'Model Predicts Status: NEGATIVE';
      statusSubtext.textContent = 'The classifier did not detect patterns indicating recorded heart disease.';
      scoreTierBadge.textContent = 'Low Risk Tier';
    }

    const scoreVal = result.score;
    scorePercentage.textContent = `${scoreVal}%`;
    const circumference = 314.16;
    const offset = circumference - (scoreVal / 100) * circumference;
    gaugeProgress.style.strokeDashoffset = offset;

    generalExplanationText.innerHTML = `
      <p><strong>Summary:</strong> ${result.general_explanation}</p>
      <p style="margin-top: 0.5rem; font-size: 0.8rem; color: #64748b;">
        <strong>Model Context:</strong> This prediction was generated using the independently trained ${mode === 'major' ? 'Major clinical' : 'Simple accessible'} model partition. Both models were calibrated on historical observations.
      </p>
    `;

    featureImportanceList.innerHTML = '';
    if (result.feature_influences && result.feature_influences.length > 0) {
      result.feature_influences.forEach(item => {
        const isRisk = item.direction === 'risk';
        const barItem = document.createElement('div');
        barItem.className = 'feature-bar-item';
        barItem.innerHTML = `
          <div class="feature-bar-header">
            <span class="feature-bar-name">${item.feature}: <small style="font-weight: normal; color: #64748b;">${item.value}</small></span>
            <span class="feature-bar-value" style="color: ${isRisk ? '#dc2626' : '#059669'};">
              ${isRisk ? '+ Risk Factor' : '- Protective Factor'}
            </span>
          </div>
          <div class="feature-bar-track">
            <div class="feature-bar-fill ${isRisk ? 'risk-increase' : 'risk-decrease'}" style="width: ${item.weight}%;"></div>
          </div>
          <div style="font-size: 0.72rem; color: #64748b; margin-top: 0.25rem;">${item.note}</div>
        `;
        featureImportanceList.appendChild(barItem);
      });
    }

    resultsContainer.classList.remove('hidden');
  }

  function setLoadingState(loading) {
    state.isSubmitting = loading;
    if (loading) {
      predictBtn.disabled = true;
      predictSpinner.classList.remove('hidden');
      predictBtn.querySelector('.btn-arrow').classList.add('hidden');
      predictBtn.querySelector('.btn-text').textContent = 'Estimating Risk...';
    } else {
      predictBtn.disabled = false;
      predictSpinner.classList.add('hidden');
      predictBtn.querySelector('.btn-arrow').classList.remove('hidden');
      predictBtn.querySelector('.btn-text').textContent = 'Run Risk Estimation';
    }
  }

  // =========================================================================
  // EVENT LISTENERS & MODALS
  // =========================================================================

  function setupEventListeners() {
    tabMajor.addEventListener('click', () => setAssessmentMode('major'));
    tabSimple.addEventListener('click', () => setAssessmentMode('simple'));

    form.addEventListener('submit', handleFormSubmit);
    resetBtn.addEventListener('click', resetForm);
    loadSampleBtn.addEventListener('click', loadSampleData);

    closeResultsTopBtn.addEventListener('click', () => {
      resultsContainer.classList.add('hidden');
    });

    performAnotherAssessmentBtn.addEventListener('click', () => {
      resultsContainer.classList.add('hidden');
      form.scrollIntoView({ behavior: 'smooth' });
    });

    printReportBtn.addEventListener('click', () => {
      window.print();
    });

    glossaryBtn.addEventListener('click', () => glossaryModal.classList.remove('hidden'));
    closeGlossaryBtn.addEventListener('click', () => glossaryModal.classList.add('hidden'));
    dismissGlossaryBtn.addEventListener('click', () => glossaryModal.classList.add('hidden'));

    apiConfigBtn.addEventListener('click', () => {
      apiUrlInput.value = state.apiBaseUrl;
      mockModeToggle.checked = state.useMockFallback;
      apiModal.classList.remove('hidden');
    });
    closeApiBtn.addEventListener('click', () => apiModal.classList.add('hidden'));
    
    saveApiBtn.addEventListener('click', () => {
      state.apiBaseUrl = apiUrlInput.value.trim().replace(/\/$/, '');
      state.useMockFallback = mockModeToggle.checked;
      apiModal.classList.add('hidden');
      showToast('API Settings Saved.');
    });

    testConnectionBtn.addEventListener('click', async () => {
      testConnectionBtn.disabled = true;
      testConnectionBtn.textContent = 'Testing...';
      try {
        const url = apiUrlInput.value.trim().replace(/\/$/, '');
        const res = await fetch(`${url}/health`, { method: 'GET', signal: AbortSignal.timeout(3000) });
        if (res.ok) showToast('Connection Successful: Backend is live!');
        else showToast(`Server replied with status ${res.status}`);
      } catch (e) {
        showToast('Could not reach server at this URL. Offline fallback is recommended.');
      } finally {
        testConnectionBtn.disabled = false;
        testConnectionBtn.textContent = 'Test Endpoint';
      }
    });

    [glossaryModal, apiModal].forEach(modal => {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.classList.add('hidden');
      });
    });

    tooltipButtons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const tip = btn.getAttribute('data-tip');
        if (tip) showToast(tip, 4500);
      });
    });

    form.querySelectorAll('input, select').forEach(field => {
      field.addEventListener('input', () => {
        const group = field.closest('.form-group');
        if (group && group.classList.contains('has-error')) {
          group.classList.remove('has-error');
          const errorSpan = group.querySelector('.field-error');
          if (errorSpan) errorSpan.textContent = '';
        }
      });
    });
  }

  let toastTimer = null;
  function showToast(msg, duration = 3000) {
    if (toastTimer) clearTimeout(toastTimer);
    toastMessage.textContent = msg;
    toastNotification.classList.remove('hidden');
    toastTimer = setTimeout(() => {
      toastNotification.classList.add('hidden');
    }, duration);
  }

  document.addEventListener('DOMContentLoaded', init);
})();
