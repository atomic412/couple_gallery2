document.addEventListener('DOMContentLoaded', () => {

    // 1. File Upload Label and Dual-Input Handling
    const fileInput = document.getElementById('file');
    const cameraInput = document.getElementById('camera');
    const fileLabelText = document.getElementById('file-chosen');
    const cameraLabelText = document.getElementById('camera-chosen');
    const submitBtn = document.getElementById('uploadBtn');

    function updateUploadState(activeInput, activeLabelText, otherInput, otherLabelText, defaultOtherText) {
        if (activeInput.files && activeInput.files.length > 0) {
            activeLabelText.textContent = activeInput.files[0].name;
            // Xóa file ở input còn lại để tránh trùng dữ liệu submit
            otherInput.value = '';
            otherLabelText.textContent = defaultOtherText;
            submitBtn.disabled = false;
        } else {
            submitBtn.disabled = true;
        }
    }

    if (fileInput && cameraInput) {
        fileInput.addEventListener('change', () => updateUploadState(fileInput, fileLabelText, cameraInput, cameraLabelText, "Chụp ảnh mới"));
        cameraInput.addEventListener('change', () => updateUploadState(cameraInput, cameraLabelText, fileInput, fileLabelText, "Từ thư viện"));

        const form = document.getElementById('uploadForm');
        const progress = document.getElementById('upload-progress');

        form.addEventListener('submit', (e) => {
            e.preventDefault(); // Ngăn trình duyệt tự động tải lại hoặc chuyển trang
            
            if (fileInput.files.length > 0 || cameraInput.files.length > 0) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang tải lên...';
                if (progress) {
                    progress.style.display = 'block';
                    progress.textContent = 'Đang tải lên...';
                }
                
                const formData = new FormData(form);
                
                fetch('/upload', {
                    method: 'POST',
                    body: formData
                }).then(() => {
                    submitBtn.innerHTML = '<i class="fas fa-check"></i> Đã tải lên!';
                    if (progress) progress.style.display = 'none';
                    form.reset();
                    fileLabelText.textContent = "Từ thư viện";
                    cameraLabelText.textContent = "Chụp ảnh mới";
                }).catch(err => {
                    submitBtn.innerHTML = 'Thử lại';
                    submitBtn.disabled = false;
                    if (progress) progress.textContent = 'Lỗi kết nối tải ảnh!';
                });
            }
        });
    }

    // 2. Love Counter (Since 08/03/2026)
    const startDate = new Date('2026-03-08T00:00:00');
    const updateCounter = () => {
        const now = new Date();
        const diffTime = Math.abs(now - startDate);
        const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
        const counterEl = document.getElementById('days-count');
        if (counterEl) {
            counterEl.innerText = diffDays;
        }
    };
    updateCounter();
    setInterval(updateCounter, 1000 * 60 * 60);

    // 3. Notes / Reminders
    const noteForm = document.getElementById('noteForm');
    const notesGrid = document.getElementById('notesGrid');
    
    function fetchNotes() {
        if (!notesGrid) return;
        fetch('/notes')
            .then(res => res.json())
            .then(data => {
                notesGrid.innerHTML = '';
                data.forEach(note => {
                    const el = document.createElement('div');
                    el.className = 'note-card';
                    el.innerHTML = `
                        <div class="note-text">${note.content}</div>
                        <div class="note-footer">
                            <span class="note-author"><i class="fas fa-pen-nib"></i> ${note.author_name}</span>
                            <span class="note-time">${note.created_at}</span>
                        </div>
                    `;
                    notesGrid.appendChild(el);
                });
            });
    }

    if (noteForm) {
        fetchNotes();
        noteForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const content = document.getElementById('noteContent').value;
            const btn = document.getElementById('noteSubmitBtn');
            btn.disabled = true;
            
            fetch('/notes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: content })
            }).then(() => {
                document.getElementById('noteContent').value = '';
                btn.disabled = false;
                fetchNotes(); // re-fetch immediately on this client
            });
        });
    }

    // 4. Notifications Permission
    if ("Notification" in window) {
        if (Notification.permission !== "granted" && Notification.permission !== "denied") {
            Notification.requestPermission();
        }
    }

    // 5. WebSocket Realtime System
    const host = window.location.host;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${host}/ws`;
    
    if (document.querySelector('.navbar')) {
        connectWebSocket(wsUrl);
    }

    // 6. Birthday Logic
    function checkBirthdays() {
        const today = new Date();
        const currentYear = today.getFullYear();
        
        // Months are 0-indexed in Date constructor! Dec = 11, Apr = 3
        const bdays = [
            { name: "Trần Hải Bằng", date: new Date(currentYear, 11, 4) },
            { name: "Trần Thị Tuyết", date: new Date(currentYear, 3, 23) }
        ];
        
        let upcoming = null;
        let minDiff = Infinity;
        
        bdays.forEach(person => {
            let nextBday = new Date(person.date);
            // Nếu đã qua sinh nhật năm nay, tính sinh nhật năm sau
            if (today.getTime() > nextBday.getTime() && (today.toDateString() !== nextBday.toDateString())) {
                nextBday.setFullYear(currentYear + 1);
            }
            
            const diffTime = nextBday - today;
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            
            if (diffDays >= 0 && diffDays < minDiff) {
                minDiff = diffDays;
                upcoming = { ...person, daysLeft: diffDays };
            }
        });
        
        // Nếu còn dưới 60 ngày thì hiển thị widget
        if (upcoming && upcoming.daysLeft <= 60) {
            const widget = document.getElementById('birthday-widget');
            const txt = document.getElementById('birthday-text');
            if (widget && txt) {
                widget.style.display = 'block';
                if (upcoming.daysLeft === 0) {
                    txt.innerHTML = `Chúc mừng sinh nhật <strong style="color:#ff6b81">${upcoming.name}</strong> nhennn! 🎁🥳🎂`;
                } else {
                    txt.innerHTML = `Chỉ còn <strong>${upcoming.daysLeft} ngày</strong> nữa là đến sinh nhật của <strong style="color:#ff6b81">${upcoming.name}</strong> rồi đó! 🥰`;
                }
            }
        }
    }
    checkBirthdays();

    // 7. Falling Hearts & Flowers Background Effect
    function createFallingElement() {
        // List of cute love-themed symbols
        const symbols = ['🌸', '💖', '🍂', '🌹', '💕', '✨', '💐', '💓', '💗'];
        const element = document.createElement('div');
        element.classList.add('falling-element');
        element.innerText = symbols[Math.floor(Math.random() * symbols.length)];
        
        // Random horizontal position
        element.style.left = Math.random() * 100 + 'vw';
        
        // Random sizes (0.8em to 2.3em)
        const size = Math.random() * 1.5 + 0.8;
        element.style.fontSize = size + 'em';
        
        // Random animation duration (fall speed: 6 to 14 seconds)
        const duration = Math.random() * 8 + 6;
        element.style.animationDuration = duration + 's';
        
        document.body.appendChild(element);
        
        // Remove element after it finishes dropping
        setTimeout(() => {
            element.remove();
        }, duration * 1000);
    }

    // Create a new falling element every 500ms
    setInterval(createFallingElement, 500);

    // 8. Bucket List Logic
    const bucketForm = document.getElementById('bucketForm');
    const bucketList = document.getElementById('bucketList');

    function fetchBuckets() {
        if (!bucketList) return;
        fetch('/bucket')
            .then(res => res.json())
            .then(data => {
                bucketList.innerHTML = '';
                data.forEach(item => {
                    const el = document.createElement('div');
                    el.className = `bucket-item ${item.is_completed ? 'completed' : ''}`;
                    el.onclick = () => toggleBucket(item.id);
                    el.innerHTML = `
                        <div class="bucket-checkbox">
                            ${item.is_completed ? '<i class="fas fa-check"></i>' : ''}
                        </div>
                        <div class="bucket-title">${item.title}</div>
                    `;
                    bucketList.appendChild(el);
                });
            });
    }

    function toggleBucket(id) {
        fetch(`/bucket/${id}/toggle`, { method: 'POST' })
            .then(() => fetchBuckets());
    }

    if (bucketForm) {
        fetchBuckets();
        bucketForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const title = document.getElementById('bucketTitle').value;
            const btn = document.getElementById('bucketSubmitBtn');
            btn.disabled = true;
            
            fetch('/bucket', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: title })
            }).then(() => {
                document.getElementById('bucketTitle').value = '';
                btn.disabled = false;
                fetchBuckets();
            });
        });
    }

    // 10. Time Capsule Logic
    const capsuleForm = document.getElementById('capsuleForm');
    const capsuleList = document.getElementById('capsuleList');

    function fetchCapsules() {
        if (!capsuleList) return;
        fetch('/capsules')
            .then(res => res.json())
            .then(data => {
                capsuleList.innerHTML = '';
                data.forEach(item => {
                    const el = document.createElement('div');
                    el.className = `capsule-item ${item.is_locked ? 'capsule-locked' : ''}`;
                    
                    let bodyHtml = '';
                    if (item.is_locked) {
                        bodyHtml = `<div class="capsule-locked-icon"><i class="fas fa-lock"></i></div>
                                    <div style="text-align:center; font-size:0.9rem; color:#888;">Mở khóa vào: <strong>${item.unlock_date}</strong></div>`;
                    } else {
                        bodyHtml = `<div class="capsule-body">${item.content}</div>`;
                    }

                    el.innerHTML = `
                        <div class="capsule-header">
                            <span><i class="fas fa-pen-nib"></i> ${item.author_name}</span>
                            <span><i class="fas fa-paper-plane"></i> Gửi ngày: ${item.created_at}</span>
                        </div>
                        ${bodyHtml}
                    `;
                    capsuleList.appendChild(el);
                });
            });
    }

    if (capsuleForm) {
        fetchCapsules();
        capsuleForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const content = document.getElementById('capsuleContent').value;
            const unlockDate = document.getElementById('capsuleDate').value;
            const btn = document.getElementById('capsuleSubmitBtn');
            btn.disabled = true;
            
            fetch('/capsules', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: content, unlock_date: unlockDate })
            }).then(() => {
                document.getElementById('capsuleContent').value = '';
                document.getElementById('capsuleDate').value = '';
                btn.disabled = false;
                fetchCapsules();
            });
        });
    }

    // 11. Love Tree Gamification
    function fetchTreeStatus() {
        const treeLevel = document.getElementById('treeLevel');
        if (!treeLevel) return;
        
        fetch('/tree-status')
            .then(res => res.json())
            .then(data => {
                treeLevel.innerText = data.level;
                document.getElementById('treeExp').innerText = data.exp;
                document.getElementById('treeNextExp').innerText = data.next_level_exp;
                document.getElementById('treeProgress').style.width = data.progress + '%';
                
                // Set Tree Emoji based on visual level
                const treeVisual = document.getElementById('treeVisual');
                const levels = ['🌱', '🌿', '🪴', '🌲', '🌳', '🌸']; // 1 to 6
                const visualLevel = Math.min(data.level, levels.length) - 1;
                treeVisual.innerText = levels[visualLevel];
            });
    }
    fetchTreeStatus();

});

function connectWebSocket(wsUrl) {
    let ws = new WebSocket(wsUrl);

    ws.onmessage = function(event) {
        const msg = event.data;
        let displayMsg = msg;
        let type = 'info';
        
        if (msg.startsWith('photo|')) {
            displayMsg = msg.replace('photo|', '');
            type = 'photo';
        } else if (msg.startsWith('note|')) {
            displayMsg = msg.replace('note|', '');
            type = 'note';
        }

        showToast(displayMsg);
        showBrowserNotification(displayMsg);
        
        // Reload page so the other user sees the new photo or note immediately
        setTimeout(() => {
            window.location.reload(); 
        }, 3000); 
    };

    ws.onclose = function(e) {
        setTimeout(function() {
            connectWebSocket(wsUrl);
        }, 2000);
    };
}

function showToast(message) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast';
    
    const icon = document.createElement('i');
    icon.className = 'fas fa-heart toast-icon';
    
    const text = document.createElement('div');
    text.className = 'toast-message';
    text.textContent = message;

    toast.appendChild(icon);
    toast.appendChild(text);
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'fadeOutRight 0.4s ease forwards';
        setTimeout(() => {
            if (toast.parentNode === container) {
                container.removeChild(toast);
            }
        }, 400); 
    }, 4500);
}

function showBrowserNotification(message) {
    if ("Notification" in window && Notification.permission === "granted") {
        new Notification("Our Album 🤍", {
            body: message,
            // icon: "/static/favicon.ico"
        });
    }
}
