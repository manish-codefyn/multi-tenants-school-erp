document.addEventListener('DOMContentLoaded', function() {
    const profilePictureForm = document.getElementById('profilePictureForm');
    const profilePictureInput = document.getElementById('profilePictureInput');
    const previewImage = document.getElementById('previewImage');
    const newPicturePreview = document.getElementById('newPicturePreview');
    const removePictureCheckbox = document.getElementById('removePicture');
    const savePictureBtn = document.getElementById('savePictureBtn');
    const pictureLoading = document.getElementById('pictureLoading');
    const currentProfilePicture = document.getElementById('currentProfilePicture');

    // Preview image when file is selected
    if (profilePictureInput) {
        profilePictureInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    previewImage.src = e.target.result;
                    previewImage.style.display = 'block';
                    newPicturePreview.style.display = 'block';
                }
                
                reader.readAsDataURL(file);
                
                // Enable the save button
                savePictureBtn.disabled = false;
            }
        });
    }

    // Handle remove picture checkbox
    if (removePictureCheckbox) {
        removePictureCheckbox.addEventListener('change', function() {
            if (this.checked) {
                profilePictureInput.disabled = true;
                newPicturePreview.style.display = 'none';
            } else {
                profilePictureInput.disabled = false;
                if (profilePictureInput.files.length > 0) {
                    newPicturePreview.style.display = 'block';
                }
            }
            savePictureBtn.disabled = false;
        });
    }

    // Handle form submission via AJAX
    if (profilePictureForm) {
        profilePictureForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            
            // Show loading
            pictureLoading.style.display = 'block';
            savePictureBtn.disabled = true;
            savePictureBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Updating...';
            
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update the profile picture on the page
                    if (data.profile_picture_url) {
                        currentProfilePicture.src = data.profile_picture_url;
                        // Also update any other instances of the profile picture on the page
                        document.querySelectorAll('.user-img, .msg-avatar').forEach(img => {
                            if (img.src.includes('avatars/avatar-2.png') || img.src.includes('profile_pictures/')) {
                                img.src = data.profile_picture_url;
                            }
                        });
                    } else {
                        // If picture was removed, set default avatar
                        currentProfilePicture.src = '/static/assets/images/avatars/avatar-2.png';
                    }
                    
                    // Show success message
                    showToast('Success', data.message, 'success');
                    
                    // Close modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('profilePictureModal'));
                    modal.hide();
                    
                    // Reset form
                    profilePictureForm.reset();
                    newPicturePreview.style.display = 'none';
                    previewImage.style.display = 'none';
                    if (removePictureCheckbox) {
                        removePictureCheckbox.checked = false;
                        profilePictureInput.disabled = false;
                    }
                    
                } else {
                    showToast('Error', data.message, 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Error', 'An error occurred while updating profile picture.', 'error');
            })
            .finally(() => {
                // Hide loading
                pictureLoading.style.display = 'none';
                savePictureBtn.disabled = false;
                savePictureBtn.innerHTML = 'Update Picture';
            });
        });
    }

    // Toast notification function
    function showToast(title, message, type) {
        // You can use your existing toast implementation or create a simple one
        const toastContainer = document.getElementById('toastContainer') || createToastContainer();
        
        const toastEl = document.createElement('div');
        toastEl.className = `toast align-items-center text-bg-${type === 'success' ? 'success' : 'danger'} border-0`;
        toastEl.setAttribute('role', 'alert');
        toastEl.setAttribute('aria-live', 'assertive');
        toastEl.setAttribute('aria-atomic', 'true');
        
        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <strong>${title}:</strong> ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        toastContainer.appendChild(toastEl);
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
        
        // Remove toast after it hides
        toastEl.addEventListener('hidden.bs.toast', function() {
            toastEl.remove();
        });
    }
    
    function createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        return container;
    }
});