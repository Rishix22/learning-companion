document.addEventListener('DOMContentLoaded', function() {
    // Tab Navigation
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            btn.classList.add('active');
            const tabId = btn.getAttribute('data-tab') + '-tab';
            document.getElementById(tabId).classList.add('active');
        });
    });

    // Enhanced Fetch with Error Handling
    async function safeFetch(url, options = {}, retries = 3) {
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            // Handle empty responses
            if (response.status === 204) return null;

            // Parse response as text first
            const text = await response.text();
            let data;
            
            try {
                data = text ? JSON.parse(text) : null;
            } catch (e) {
                throw new Error(`Invalid JSON received: ${text.substring(0, 100)}...`);
            }

            if (!response.ok) {
                throw new Error(data?.error || `HTTP error! status: ${response.status}`);
            }

            return data;
        } catch (error) {
            if (retries > 0) {
                await new Promise(resolve => setTimeout(resolve, 1000));
                return safeFetch(url, options, retries - 1);
            }
            throw error;
        }
    }

    // Profile Management
    const profileForm = document.getElementById('profile-form');
    profileForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = profileForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        
        try {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner"></span> Saving...';
            
            const response = await safeFetch('/api/user_profile', {
                method: 'POST',
                body: JSON.stringify({
                    name: document.getElementById('name').value,
                    learning_style: document.getElementById('learning-style').value,
                    knowledge_level: parseInt(document.getElementById('knowledge-level').value)
                })
            });

            showToast('Profile saved successfully!', 'success');
        } catch (error) {
            showToast(`Failed to save: ${error.message}`, 'error');
            console.error('Profile error:', error);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    });

    // Learning System
    const learnForm = document.getElementById('learn-form');
    learnForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const topicInput = document.getElementById('topic');
        const submitBtn = learnForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        
        if (!topicInput.value.trim()) {
            showToast('Please enter a topic', 'warning');
            return;
        }

        try {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner"></span> Searching...';
            
            const content = await safeFetch('/api/learn', {
                method: 'POST',
                body: JSON.stringify({ topic: topicInput.value.trim() })
            });

            document.getElementById('content-title').textContent = content.title || topicInput.value;
            document.getElementById('content-body').innerHTML = 
                content.content || '<em>No content available</em>';
            document.getElementById('learning-content').classList.remove('hidden');
        } catch (error) {
            showToast(`Failed to load: ${error.message}`, 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    });

    // Save Material
    document.getElementById('save-material').addEventListener('click', async function() {
        const btn = this;
        const originalText = btn.textContent;
        
        try {
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner"></span> Saving...';
            
            await safeFetch('/api/save_material', {
                method: 'POST',
                body: JSON.stringify({
                    topic: document.getElementById('content-title').textContent,
                    content: document.getElementById('content-body').innerHTML
                })
            });

            showToast('Material saved for review!', 'success');
            loadReviewItems();
        } catch (error) {
            showToast(`Save failed: ${error.message}`, 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = originalText;
        }
    });

    // Review System
    async function loadReviewItems() {
        const reviewList = document.getElementById('review-list');
        reviewList.innerHTML = '<div class="loading-msg">Loading reviews...</div>';
        
        try {
            const items = await safeFetch('/api/get_reviews');
            reviewList.innerHTML = '';
            
            if (!items || items.length === 0) {
                reviewList.innerHTML = '<div class="empty-msg">No reviews due yet!</div>';
                return;
            }

            items.forEach(item => {
                const reviewItem = document.createElement('div');
                reviewItem.className = 'review-item';
                reviewItem.innerHTML = `
                    <h4>${item.topic}</h4>
                    <small>${formatDate(item.next_review)}</small>
                    <div class="content-preview">${item.content.substring(0, 100)}...</div>
                `;
                reviewItem.addEventListener('click', () => startReview(item));
                reviewList.appendChild(reviewItem);
            });
        } catch (error) {
            reviewList.innerHTML = `<div class="error-msg">Error loading reviews: ${error.message}</div>`;
        }
    }

    function startReview(item) {
        document.getElementById('review-title').textContent = item.topic;
        document.getElementById('review-content').innerHTML = item.content;
        document.getElementById('review-interface').classList.remove('hidden');
        
        // Clear previous handlers
        document.querySelectorAll('.rating-btn').forEach(btn => btn.onclick = null);
        
        // Set new handlers
        document.querySelectorAll('.rating-btn').forEach(btn => {
            btn.onclick = async () => {
                const rating = parseInt(btn.getAttribute('data-rating'));
                const originalText = btn.textContent;
                
                try {
                    btn.disabled = true;
                    btn.innerHTML = '<span class="spinner"></span>';
                    
                    const result = await safeFetch('/api/review', {
                        method: 'POST',
                        body: JSON.stringify({
                            material_id: item.id,
                            performance: rating
                        })
                    });

                    showToast(`Reviewed! Next in ${result.interval_days} days`, 'success');
                    document.getElementById('review-interface').classList.add('hidden');
                    loadReviewItems();
                } catch (error) {
                    showToast(`Review failed: ${error.message}`, 'error');
                } finally {
                    btn.disabled = false;
                    btn.textContent = originalText;
                }
            };
        });
    }

    // Helper Functions
    function formatDate(dateStr) {
        if (!dateStr) return 'New material';
        const date = new Date(dateStr);
        return `Due: ${date.toLocaleDateString()}`;
    }

    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('fade-out');
            setTimeout(() => toast.remove(), 500);
        }, 3000);
    }

    // Initialize
    loadReviewItems();
});