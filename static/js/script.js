let uploadedVideoPath = null;
let isWebcam = false;
let dashboardInterval = null;

// Ensure consistent state on load
document.addEventListener('DOMContentLoaded', () => {
    // Explicitly hide the cancel button on load to prevent UI glitches
    const cancelBtn = document.getElementById('cancelWebcamBtn');
    if (cancelBtn) cancelBtn.style.display = 'none';
});

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
    
    // Reset Text
    const uploadText = document.getElementById('uploadStatusText');
    if (uploadText) uploadText.innerText = "Drag and drop your video file here";
    
    // Reset Zone Styling
    const zone = document.querySelector('.upload-zone');
    if (zone) {
        zone.style.borderColor = 'rgba(0,0,0,0.1)'; 
        zone.style.background = 'rgba(255,255,255,0.3)'; 
    }
    
    // Hide Button
    const removeBtn = document.getElementById('removeFileBtn');
    if (removeBtn) removeBtn.style.display = 'none';
}

// --- 2. WEBCAM LOGIC (Corrected) ---
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
    
    // Show Cancel, Hide Webcam button
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
        inputField.style.border = "1px solid #2a2a35"; // Resetting to default style
        inputField.style.color = "var(--text-main)";
    }

    // Hide Cancel, Show Webcam button
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

            if (user && pass) {
                if (rawUrl.includes('@')) {
                    finalSource = rawUrl; 
                } else {
                    const parts = rawUrl.split('://');
                    if (parts.length === 2) {
                        finalSource = `${parts[0]}://${user}:${pass}@${parts[1]}`;
                    } else {
                        finalSource = rawUrl; 
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
            tag.className = 'overlay-tag'; // Using consistent styling
            tag.style.position = 'relative';
            tag.style.top = '0';
            tag.style.left = '0';
            tag.style.marginRight = '5px';
            tag.innerHTML = `<i class="fas fa-check-circle"></i> ${row.querySelector('h4').innerText}`;
            tagsContainer.appendChild(tag);
        }
    });

    if (activeModels.includes('shoplift')) {
        if (!activeModels.includes('face')) activeModels.push('face');
        if (!activeModels.includes('headwear')) activeModels.push('headwear');
    }

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
        document.getElementById('videoStream').style.display = "block"; 
        
        setTimeout(() => {
            document.getElementById('monitoringScreen').style.opacity = '1';
        }, 50);

        if (dashboardInterval) clearInterval(dashboardInterval);
        dashboardInterval = setInterval(updateDashboard, 1000); 
        console.log("Dashboard polling started..."); 

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
    if (!monitoringScreen || monitoringScreen.style.display === 'none') return;

    fetch('/api/dashboard_data')
        .then(response => response.json())
        .then(data => {
            if (data.alerts && data.alerts.length > 0) {
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
        .catch(err => console.log("Dashboard update skipped or idle"));
}

// --- 6. BACK BUTTON ---
function backToConfig() {
    const videoStream = document.getElementById('videoStream');
    if (videoStream) {
        videoStream.style.display = 'none'; 
        videoStream.src = "";
        videoStream.removeAttribute("src"); 
    }

    if (dashboardInterval) {
        clearInterval(dashboardInterval);
        dashboardInterval = null;
    }
    
    fetch('/api/reset_session', { method: 'POST' }).catch(err => console.log(err));
    
    try {
        cancelWebcam(); 
    } catch(e) { console.log("Webcam reset skipped"); }

    const alertList = document.getElementById('alert-list-container');
    const alertCount = document.getElementById('alert-count');
    if (alertList) alertList.innerHTML = '<div style="padding: 10px; color: #666; font-size: 12px;">Waiting for events...</div>';
    if (alertCount) alertCount.innerText = "0 events";

    const configScreen = document.getElementById('configScreen');
    const monitoringScreen = document.getElementById('monitoringScreen');

    if (monitoringScreen && configScreen) {
        monitoringScreen.style.display = 'none';
        monitoringScreen.style.opacity = '0';
        
        configScreen.style.display = 'block';
        setTimeout(() => {
            configScreen.style.opacity = '1';
        }, 10);
    }
}

// Tab Switching Logic
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