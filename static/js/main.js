/* ── ChainTrack -- Client-side JavaScript ──────────────────────────────── */

// ── Quick Track ──────────────────────────────────────────────────────────

function quickTrack(e) {
    e.preventDefault();
    const input = document.getElementById('quick-track-input');
    const trackingId = input.value.trim();
    if (trackingId) {
        window.location.href = '/track/' + encodeURIComponent(trackingId);
    }
}

// ── Create Product ───────────────────────────────────────────────────────

async function createProduct(e) {
    e.preventDefault();
    const resultEl = document.getElementById('product-result');

    const payload = {
        name: document.getElementById('prod-name').value.trim(),
        sku: document.getElementById('prod-sku').value.trim(),
        category: document.getElementById('prod-category').value,
        manufacturer: document.getElementById('prod-manufacturer').value.trim(),
        weight_kg: parseFloat(document.getElementById('prod-weight').value) || 0,
        description: document.getElementById('prod-description').value.trim(),
    };

    if (!payload.name || !payload.sku) {
        showResult(resultEl, 'error', 'Product name and SKU are required.');
        return;
    }

    try {
        const resp = await fetch('/api/products', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail || 'Failed to create product');
        }

        const product = await resp.json();
        showResult(
            resultEl,
            'success',
            '<strong>Product registered!</strong> ' +
            'Tracking ID: <a href="/track/' + product.tracking_id + '">' +
            product.tracking_id + '</a> | ' +
            'Chain genesis block created.'
        );

        // Reset form
        document.getElementById('product-form').reset();

        // Reload after short delay to update table
        setTimeout(() => window.location.reload(), 1500);

    } catch (err) {
        showResult(resultEl, 'error', 'Error: ' + err.message);
    }
}

// ── Record Event ─────────────────────────────────────────────────────────

async function recordEvent(e) {
    e.preventDefault();
    const resultEl = document.getElementById('event-result');

    const payload = {
        product_id: document.getElementById('event-product').value,
        event_type: document.getElementById('event-type').value,
        location: document.getElementById('event-location').value.trim(),
        actor: document.getElementById('event-actor').value.trim(),
        event_data: '{}',
    };

    if (!payload.product_id) {
        showResult(resultEl, 'error', 'Please select a product.');
        return;
    }

    try {
        const resp = await fetch('/api/chain/event', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail || 'Failed to record event');
        }

        const block = await resp.json();
        showResult(
            resultEl,
            'success',
            '<strong>Event recorded!</strong> ' +
            'Block #' + block.block_index + ' created. ' +
            'Hash: <code>' + block.block_hash.substring(0, 16) + '...</code>'
        );

        // Reset form
        document.getElementById('event-form').reset();
        setTimeout(() => window.location.reload(), 1500);

    } catch (err) {
        showResult(resultEl, 'error', 'Error: ' + err.message);
    }
}

// ── Verify Chain ─────────────────────────────────────────────────────────

async function verifyChain(e) {
    e.preventDefault();
    const productId = document.getElementById('verify-product').value;
    if (!productId) return;

    await runVerification('/api/verify/' + productId);
}

async function verifyByTracking(e) {
    e.preventDefault();
    const trackingId = document.getElementById('verify-tracking-input').value.trim();
    if (!trackingId) return;

    await runVerification('/api/verify/tracking/' + encodeURIComponent(trackingId));
}

async function runVerification(url) {
    const resultsEl = document.getElementById('verify-results');
    const animEl = document.getElementById('verify-animation');
    const progressBar = document.getElementById('verify-progress-bar');
    const statusText = document.getElementById('verify-status-text');
    const outcomeEl = document.getElementById('verify-outcome');
    const bannerEl = document.getElementById('verify-banner');
    const detailsEl = document.getElementById('verify-details');

    // Show animation
    resultsEl.style.display = 'block';
    animEl.style.display = 'block';
    outcomeEl.style.display = 'none';
    progressBar.style.width = '0%';
    statusText.textContent = 'Initializing verification...';

    // Animate progress bar
    let progress = 0;
    const animInterval = setInterval(() => {
        progress = Math.min(progress + Math.random() * 15, 85);
        progressBar.style.width = progress + '%';

        if (progress < 30) {
            statusText.textContent = 'Walking hash chain...';
        } else if (progress < 60) {
            statusText.textContent = 'Recomputing SHA-256 hashes...';
        } else {
            statusText.textContent = 'Verifying block linkage...';
        }
    }, 200);

    try {
        const resp = await fetch(url);
        clearInterval(animInterval);

        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail || 'Verification failed');
        }

        const result = await resp.json();

        // Complete the progress bar
        progressBar.style.width = '100%';
        statusText.textContent = 'Verification complete!';

        setTimeout(() => {
            animEl.style.display = 'none';
            outcomeEl.style.display = 'block';

            if (result.is_valid) {
                bannerEl.className = 'verification-banner valid';
                bannerEl.innerHTML = '&#x2705; <strong>Chain Verified:</strong> ' +
                    'All ' + result.total_blocks + ' blocks are authentic and untampered.';
            } else {
                bannerEl.className = 'verification-banner invalid';
                bannerEl.innerHTML = '&#x26a0; <strong>TAMPER DETECTED:</strong> ' +
                    result.tampered_blocks.length + ' of ' + result.total_blocks +
                    ' blocks failed hash verification.';
            }

            let details = 'Product ID: ' + result.product_id + '\n';
            if (result.tracking_id) {
                details += 'Tracking ID: ' + result.tracking_id + '\n';
            }
            details += 'Total Blocks: ' + result.total_blocks + '\n';
            details += 'Verified Blocks: ' + result.verified_blocks + '\n';
            details += 'Chain Valid: ' + (result.is_valid ? 'YES' : 'NO') + '\n';
            if (result.tampered_blocks.length > 0) {
                details += 'Tampered Indices: ' + result.tampered_blocks.join(', ') + '\n';
            }
            details += '\n' + result.message;

            detailsEl.textContent = details;
        }, 500);

    } catch (err) {
        clearInterval(animInterval);
        progressBar.style.width = '100%';
        progressBar.style.background = '#e74c3c';
        statusText.textContent = 'Error: ' + err.message;
    }
}

// ── QR Modal ─────────────────────────────────────────────────────────────

function showQR(base64Data, trackingId) {
    const modal = document.getElementById('qr-modal');
    const img = document.getElementById('qr-image');
    const title = document.getElementById('qr-title');

    img.src = 'data:image/png;base64,' + base64Data;
    title.textContent = 'QR Code: ' + trackingId;
    modal.style.display = 'flex';
}

function closeQR(e) {
    if (e.target === document.getElementById('qr-modal')) {
        document.getElementById('qr-modal').style.display = 'none';
    }
}

// ── Utility ──────────────────────────────────────────────────────────────

function showResult(el, type, html) {
    el.style.display = 'block';
    el.className = 'result-panel ' + type;
    el.innerHTML = html;
}

// ── Chain Block Animation on Scroll ──────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    // Animate chain blocks into view
    const blocks = document.querySelectorAll('.chain-block');
    if (blocks.length > 0 && 'IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        blocks.forEach((block, i) => {
            block.style.opacity = '0';
            block.style.transform = 'translateY(20px)';
            block.style.transition = 'opacity 0.4s ease ' + (i * 0.1) + 's, transform 0.4s ease ' + (i * 0.1) + 's';
            observer.observe(block);
        });
    }

    // Keyboard shortcut: Escape to close modal
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const modal = document.getElementById('qr-modal');
            if (modal) modal.style.display = 'none';
        }
    });
});
