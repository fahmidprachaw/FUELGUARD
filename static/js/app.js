/**
 * FuelGuard Frontend — app.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Handles:
 *   - Image drag-and-drop and file selection
 *   - Image preview
 *   - Form submission via fetch() with FormData
 *   - CSRF token handling (required by Django)
 *   - Dynamic result rendering
 * ─────────────────────────────────────────────────────────────────────────────
 */

'use strict';

// ─── CSRF Helper ─────────────────────────────────────────────────────────────
/**
 * Read the CSRF token from Django's cookie.
 * Django sets a cookie named 'csrftoken' that must be sent back
 * in the X-CSRFToken header for all non-GET requests.
 *
 * @param {string} name  - Cookie name to look for ('csrftoken')
 * @returns {string|null} - Token string or null if not found
 */
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}


// ─── Image Handling ───────────────────────────────────────────────────────────

/**
 * Handle image file selected via <input type="file">
 */
function handleFileSelect(event) {
  const file = event.target.files[0];
  if (file) {
    showPreview(file);
  }
}

/**
 * Prevent default drag behavior and add visual cue
 */
function handleDragOver(event) {
  event.preventDefault();
  event.stopPropagation();
  document.getElementById('drop-zone').classList.add('dragover');
}

/**
 * Remove visual cue when drag leaves
 */
function handleDragLeave(event) {
  event.preventDefault();
  document.getElementById('drop-zone').classList.remove('dragover');
}

/**
 * Handle image dropped onto the drop zone
 */
function handleDrop(event) {
  event.preventDefault();
  event.stopPropagation();
  document.getElementById('drop-zone').classList.remove('dragover');

  const file = event.dataTransfer.files[0];
  if (file && file.type.startsWith('image/')) {
    // Attach the dropped file to the hidden <input> so FormData picks it up
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    document.getElementById('image-input').files = dataTransfer.files;

    showPreview(file);
  } else {
    showToast('Please drop a valid image file.', 'warning');
  }
}

/**
 * Show image preview in the drop zone
 *
 * @param {File} file - The image file to preview
 */
function showPreview(file) {
  const reader = new FileReader();

  reader.onload = function(e) {
    const previewImg  = document.getElementById('preview-img');
    const fileName    = document.getElementById('file-name');
    const placeholder = document.getElementById('upload-placeholder');
    const preview     = document.getElementById('upload-preview');

    previewImg.src = e.target.result;
    fileName.textContent = file.name;

    placeholder.classList.add('hidden');
    preview.classList.remove('hidden');
    preview.classList.add('flex');
  };

  reader.readAsDataURL(file);  // Read file as base64 URL for preview
}

/**
 * Clear the selected image and reset drop zone
 *
 * @param {Event} event - Click event (stopPropagation prevents re-opening picker)
 */
function clearImage(event) {
  event.stopPropagation();  // Prevent click from bubbling to drop zone

  document.getElementById('image-input').value = '';
  document.getElementById('preview-img').src = '';
  document.getElementById('file-name').textContent = '';

  document.getElementById('upload-placeholder').classList.remove('hidden');
  document.getElementById('upload-preview').classList.remove('flex');
  document.getElementById('upload-preview').classList.add('hidden');

  // Also clear any result
  hideResult();
}


// ─── Form Submission ──────────────────────────────────────────────────────────

/**
 * Main handler: builds FormData, calls API, renders result.
 * Called when user clicks "CHECK VEHICLE".
 */
async function submitCheck() {
  const imageInput    = document.getElementById('image-input');
  const manualNumber  = document.getElementById('manual-number').value.trim().toUpperCase();

  // Require at least one input: image OR manual number
  if (!imageInput.files.length && !manualNumber) {
    showToast('Please upload an image or enter a vehicle number.', 'warning');
    return;
  }

  // ── Build FormData ────────────────────────────────────────────────────────
  const formData = new FormData();

  if (imageInput.files.length > 0) {
    formData.append('image', imageInput.files[0]);  // Key must match serializer field
  }

  if (manualNumber) {
    formData.append('manual_number', manualNumber);
  }

  // ── Set loading state ─────────────────────────────────────────────────────
  setLoading(true);
  hideResult();

  // ── Call the API ──────────────────────────────────────────────────────────
  try {
    const response = await fetch('/api/check-fuel/', {
      method: 'POST',
      headers: {
        // Django CSRF protection: include token from cookie in header
        'X-CSRFToken': getCookie('csrftoken'),
        // Note: Do NOT set Content-Type here; browser sets it automatically
        // with the correct multipart boundary for FormData
      },
      body: formData,
    });

    // Parse the JSON response body
    const data = await response.json();
    console.log('[FuelGuard] API response:', data);

    // ── Render result ─────────────────────────────────────────────────────
    renderResult(data);

  } catch (error) {
    console.error('[FuelGuard] Fetch error:', error);
    renderResult({
      status: 'error',
      message: 'Network error. Please check your connection and try again.'
    });
  } finally {
    setLoading(false);
  }
}


// ─── Result Rendering ─────────────────────────────────────────────────────────

/**
 * Renders the API response as a styled card.
 *
 * @param {Object} data - API JSON response
 * @param {string} data.status  - 'allowed' | 'blocked' | 'error'
 * @param {string} [data.number]  - Vehicle number
 * @param {string} [data.message] - Human-readable message
 */
function renderResult(data) {
  const section = document.getElementById('result-section');
  section.classList.remove('hidden');

  let html = '';

  if (data.status === 'allowed') {
    // ── GREEN: Fuel allowed ────────────────────────────────────────────────
    html = `
      <div class="result-allowed rounded-xl border p-5 animate-slide-up">
        <div class="flex items-start gap-4">
          <div class="flex-shrink-0 w-10 h-10 rounded-full bg-green-500/20 flex items-center justify-center">
            <svg class="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
          </div>
          <div class="flex-1">
            <p class="text-green-300 font-semibold text-sm uppercase tracking-wide mb-1">✅ Fuel Allowed</p>
            <p class="plate-display text-white">${escapeHtml(data.number)}</p>
            <p class="text-green-400/80 text-xs mt-2">${escapeHtml(data.message || '')}</p>
            ${data.fueled_at ? `<p class="text-zinc-500 text-xs mt-1">Fueled at: ${escapeHtml(data.fueled_at)}</p>` : ''}
          </div>
        </div>
      </div>`;

  } else if (data.status === 'blocked') {
    // ── RED: Vehicle blocked ───────────────────────────────────────────────
    html = `
      <div class="result-blocked rounded-xl border p-5 animate-slide-up">
        <div class="flex items-start gap-4">
          <div class="flex-shrink-0 w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center">
            <svg class="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636
                   m12.728 12.728L5.636 5.636"/>
            </svg>
          </div>
          <div class="flex-1">
            <p class="text-red-300 font-semibold text-sm uppercase tracking-wide mb-1">🚫 Fuel Blocked</p>
            <p class="plate-display text-white">${escapeHtml(data.number)}</p>
            ${data.next_refuel_date ? `<p class="text-red-300 text-xs mt-1">🕐 Next refuel allowed: <span class="font-semibold">${escapeHtml(data.next_refuel_date)}</span></p>` : ''}
            <p class="text-red-400/80 text-xs mt-2">${escapeHtml(data.message || '')}</p>
            ${data.last_fuel_date ? `<p class="text-zinc-500 text-xs mt-1">Last fueled: ${escapeHtml(data.last_fuel_date)}</p>` : ''}
          </div>
        </div>
      </div>`;

  } else {
    // ── YELLOW: Error / OCR failure ────────────────────────────────────────
    html = `
      <div class="result-error rounded-xl border p-5 animate-slide-up">
        <div class="flex items-start gap-4">
          <div class="flex-shrink-0 w-10 h-10 rounded-full bg-yellow-500/20 flex items-center justify-center">
            <svg class="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667
                   1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464
                   0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
            </svg>
          </div>
          <div class="flex-1">
            <p class="text-yellow-300 font-semibold text-sm uppercase tracking-wide mb-1">⚠️ Detection Error</p>
            <p class="text-yellow-200/80 text-sm mt-1">${escapeHtml(data.message || 'Unknown error')}</p>
            <p class="text-zinc-500 text-xs mt-2">Try a clearer image or use the manual input field above.</p>
          </div>
        </div>
      </div>`;
  }

  section.innerHTML = html;

  // Smooth scroll to result
  section.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Hide the result section
 */
function hideResult() {
  const section = document.getElementById('result-section');
  section.classList.add('hidden');
  section.innerHTML = '';
}


// ─── UI Helpers ───────────────────────────────────────────────────────────────

/**
 * Toggle the submit button loading state
 *
 * @param {boolean} isLoading
 */
function setLoading(isLoading) {
  const btn     = document.getElementById('submit-btn');
  const btnText = document.getElementById('btn-text');
  const btnIcon = document.getElementById('btn-icon');
  const spinner = document.getElementById('btn-spinner');

  btn.disabled = isLoading;

  if (isLoading) {
    btnText.textContent = 'SCANNING...';
    btnIcon.classList.add('hidden');
    spinner.classList.remove('hidden');
  } else {
    btnText.textContent = 'CHECK VEHICLE';
    btnIcon.classList.remove('hidden');
    spinner.classList.add('hidden');
  }
}

/**
 * Show a brief toast notification
 *
 * @param {string} message - Text to show
 * @param {'warning'|'info'} type - Style variant
 */
function showToast(message, type = 'info') {
  // Remove any existing toast
  const existingToast = document.getElementById('toast');
  if (existingToast) existingToast.remove();

  const colors = {
    warning: 'bg-yellow-900/90 border-yellow-600 text-yellow-200',
    info:    'bg-blue-900/90 border-blue-600 text-blue-200',
  };

  const toast = document.createElement('div');
  toast.id = 'toast';
  toast.className = `fixed top-4 right-4 z-50 px-4 py-3 rounded-lg border text-sm
                     ${colors[type]} backdrop-blur animate-fade-in shadow-xl max-w-xs`;
  toast.textContent = message;

  document.body.appendChild(toast);

  // Auto-remove after 3 seconds
  setTimeout(() => toast.remove(), 3000);
}

/**
 * Escape HTML to prevent XSS when inserting API data into innerHTML
 *
 * @param {string} str
 * @returns {string}
 */
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}


// ─── Keyboard shortcut: Enter submits ─────────────────────────────────────────
document.addEventListener('keydown', function(e) {
  if (e.key === 'Enter' && !e.target.matches('input[type="text"]')) {
    submitCheck();
  }
});

// Allow Enter key in manual input field to submit
document.addEventListener('DOMContentLoaded', function() {
  const manualInput = document.getElementById('manual-number');
  if (manualInput) {
    manualInput.addEventListener('keydown', function(e) {
      if (e.key === 'Enter') submitCheck();
    });
  }
});
