let uploadedVideoPath = null;
let isWebcam = false;
let dashboardInterval = null; // [NEW] To stop logs when leaving page

// --- 1. FILE UPLOAD LOGIC ---
const fileInput = document.getElementById('fileInput');
if (fileInput) {
    fileInput.addEventListener('change', async function(e) {
        const file = e.target.files[0];
        if (!file) return;

        const uploadText = document.getElementById('uploadStatusText');
        const removeBtn = document.getElementById('removeFileBtn');
        const originalText = "Drag and drop your video file here";

        uploadText.innerText = "Uploading...";
        
        const formData = new FormData();
        formData.append('video', file);

        try {
            const response = await fetch('/upload_video', { method: 'POST', body: formData });
            const data = await response.json();

            if (response.ok) {
                uploadedVideoPath = data.filepath;
                uploadText.innerText = "✅ Ready: " + file.name;
                const zone = document.querySelector('.upload-zone');
                if (zone) {
                    zone.style.borderColor = '#2ed573';
                    zone.style.background = 'rgba(46, 213, 115, 0.1)';
                }
                if (removeBtn) removeBtn.style.display = 'flex';
                isWebcam = false; 
            } else {
                alert("Error: " + data.error);
                uploadText.innerText = originalText;
            }
        } catch (err) {
            console.error(err);
            uploadText.innerText = originalText;
        }
    });
}

function removeUploadedFile(event) {
    event.stopPropagation();
    uploadedVideoPath = null;
    document.getElementById('fileInput').value = "";
    
    const uploadText = document.getElementById('uploadStatusText');
    if (uploadText) uploadText.innerText = "Drag and drop your video file here";
    
    const zone = document.querySelector('.upload-zone');
    if (zone) {
        zone.style.borderColor = '#333';
        zone.style.background = 'transparent';
    }
    const removeBtn = document.getElementById('removeFileBtn');
    if (removeBtn) removeBtn.style.display = 'none';
}

// --- 2. WEBCAM LOGIC (Safe Version) ---
function useWebcam() {
    const inputField = document.getElementById('rtspUrl');
    const cancelBtn = document.getElementById('cancelWebcamBtn');
    const webcamBtn = document.getElementById('webcamBtn');

    if (inputField) {
        inputField.value = "Webcam Selected";
        inputField.disabled = true;
        inputField.style.opacity = "0.8";
        inputField.style.border = "1px solid #2ed573";
        inputField.style.color = "#2ed573";
    }
    
    // Safety checks in case button IDs are missing in HTML
    if (cancelBtn) cancelBtn.style.display = "inline-flex";
    if (webcamBtn) webcamBtn.style.display = "none";
    
    isWebcam = true;
}

function cancelWebcam() {
    const inputField = document.getElementById('rtspUrl');
    const cancelBtn = document.getElementById('cancelWebcamBtn');
    const webcamBtn = document.getElementById('webcamBtn');

    if (inputField) {
        inputField.value = "";
        inputField.disabled = false;
        inputField.style.opacity = "1";
        inputField.style.border = "1px solid #2a2a35";
        inputField.style.color = "white";
    }

    if (cancelBtn) cancelBtn.style.display = "none";
    if (webcamBtn) webcamBtn.style.display = "inline-flex";

    isWebcam = false;
}

// --- 3. MODEL SELECTION ---
function toggleAllModels(shouldSelect) {
    document.querySelectorAll('.model-row input[type="checkbox"]').forEach(cb => {
        cb.checked = shouldSelect;
    });
}

// --- 4. START SURVEILLANCE ---
// --- 4. START SURVEILLANCE ---
function startSurveillance() {
    const activeTab = document.querySelector('.tab-btn.active').getAttribute('data-tab');
    let finalSource = "";
    let sessionName = "Unknown";
    
    if (activeTab === 'upload') {
        if (!uploadedVideoPath) {
            alert("⚠️ Please upload a video file first!");
            return;
        }
        finalSource = uploadedVideoPath;
        sessionName = "Video_Upload";
    } else {
        // IP Tab Logic
        if (isWebcam) {
            finalSource = "0";
            sessionName = "Webcam";
        } else {
            const rawUrl = document.getElementById('rtspUrl').value.trim();
            const user = document.getElementById('rtspUser').value.trim();
            const pass = document.getElementById('rtspPass').value.trim();

            if (!rawUrl) {
                alert("⚠️ Please enter a Camera URL (RTSP or HTTP).");
                return;
            }

            // Logic to inject credentials for both RTSP and HTTP
            if (user && pass) {
                if (rawUrl.includes('@')) {
                    finalSource = rawUrl; // Credentials already in URL
                } else {
                    // Inject user:pass after the protocol (e.g., http://user:pass@192...)
                    const parts = rawUrl.split('://');
                    if (parts.length === 2) {
                        finalSource = `${parts[0]}://${user}:${pass}@${parts[1]}`;
                    } else {
                        finalSource = rawUrl; // Fallback
                    }
                }
            } else {
                finalSource = rawUrl;
            }
            
            sessionName = "IP_Camera";
        }
    }

    const sessionId = `${sessionName}_${Date.now()}`;

    // Gather Models
    const activeModels = [];
    const tagsContainer = document.getElementById('activeModelTags');
    tagsContainer.innerHTML = ''; 

    document.querySelectorAll('.model-row').forEach(row => {
        const checkbox = row.querySelector('input[type="checkbox"]');
        if (checkbox && checkbox.checked) {
            activeModels.push(row.getAttribute('data-model'));
            const tag = document.createElement('span');
            tag.className = 'tag';
            tag.innerHTML = `<i class="fas fa-check-circle"></i> ${row.querySelector('h4').innerText}`;
            tagsContainer.appendChild(tag);
        }
    });

    if (activeModels.length === 0) {
        alert("⚠️ Please select at least one AI Model!");
        return;
    }

    const streamUrl = `/video_feed?source=${encodeURIComponent(finalSource)}&models=${activeModels.join(',')}&session=${sessionId}`;

    document.getElementById('configScreen').style.opacity = '0';
    setTimeout(() => {
        document.getElementById('configScreen').style.display = 'none';
        document.getElementById('monitoringScreen').style.display = 'block';
        document.getElementById('videoStream').src = streamUrl;
        
        setTimeout(() => {
            document.getElementById('monitoringScreen').style.opacity = '1';
        }, 50);

        // ---  ADD THIS BLOCK HERE ---
        // Start polling the server for alerts every 1 second
        if (dashboardInterval) clearInterval(dashboardInterval); // clear any old ones
        dashboardInterval = setInterval(updateDashboard, 1000); 
        console.log("Dashboard polling started..."); 
        // -----------------------------

    }, 400);
}

// --- 5. IMAGE VIEWER & DASHBOARD ---
function openImage(base64Data) {
    if (!base64Data) return;
    const modal = document.getElementById('imageModal');
    const modalImg = document.getElementById('fullImage');
    if (modal && modalImg) {
        modal.style.display = "block";
        modalImg.src = base64Data;
    }
}

function closeModal() {
    const modal = document.getElementById('imageModal');
    if (modal) modal.style.display = "none";
}

window.onclick = function(event) {
    const modal = document.getElementById('imageModal');
    if (event.target == modal) {
        modal.style.display = "none";
    }
}

function updateDashboard() {
    const monitoringScreen = document.getElementById('monitoringScreen');
    // Double check to prevent background polling
    if (!monitoringScreen || monitoringScreen.style.display === 'none') return;

    fetch('/api/dashboard_data')
        .then(response => response.json())
        .then(data => {
            
            if (data.alerts.length > 0) {
                const alertCount = document.getElementById('alert-count');
                const alertList = document.getElementById('alert-list-container');
                
                if (alertCount) alertCount.innerText = "Latest Events";
                if (alertList) {
                    let html = '';
                    data.alerts.forEach(alert => {
                        let severity = (alert.event === 'FIRE' || alert.event === 'THEFT') ? 'critical' : 'warning';
                        html += `
                            <div class="alert-card ${severity}" onclick="openImage('${alert.image_url}')">
                                <div class="alert-thumb" style="background-image: url('${alert.image_url}'); background-size: cover; background-position: center;"></div>
                                <div class="alert-details">
                                    <span class="time">${alert.time_short}</span>
                                    <p>${alert.event} - ID: ${alert.person_id}</p>
                                </div>
                                <span class="level"><i class="fas fa-expand"></i> VIEW</span>
                            </div>
                        `;
                    });
                    alertList.innerHTML = html;
                }
            }
        })
        .catch(err => console.log("Dashboard update skipped"));
}

// --- 6. BACK BUTTON (FIXED) ---
function backToConfig() {
    // 1. Stop Video
    const videoStream = document.getElementById('videoStream');
    if (videoStream) {
        videoStream.src = "";
        videoStream.removeAttribute("src"); // Force kill connection
    }

    // 2. Stop Polling Logs
    if (dashboardInterval) {
        clearInterval(dashboardInterval);
        dashboardInterval = null;
    }
    
    // 3. Reset Session on Server
    fetch('/api/reset_session', { method: 'POST' });
    
    // 4. Safe UI Reset (Checks if elements exist first)
    try {
        cancelWebcam(); // Attempt to reset webcam
    } catch(e) { console.log("Webcam reset skipped"); }

    const alertList = document.getElementById('alert-list-container');
    const alertCount = document.getElementById('alert-count');
    if (alertList) alertList.innerHTML = '<div style="padding: 10px; color: #666;">Waiting for events...</div>';
    if (alertCount) alertCount.innerText = "0 events";

    // 5. Visual Transition
    const configScreen = document.getElementById('configScreen');
    const monitoringScreen = document.getElementById('monitoringScreen');

    if (monitoringScreen && configScreen) {
        monitoringScreen.style.opacity = '0';
        setTimeout(() => {
            monitoringScreen.style.display = 'none';
            configScreen.style.display = 'block';
            setTimeout(() => {
                configScreen.style.opacity = '1';
            }, 50);
        }, 400);
    }
}

// Helpers
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.style.display = 'none');
        btn.classList.add('active');
        const tabId = btn.getAttribute('data-tab');
        const content = document.getElementById(tabId + 'Tab');
        if (content) content.style.display = 'block';
    });
});
