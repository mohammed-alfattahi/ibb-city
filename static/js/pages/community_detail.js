/**
 * Community Detail Interaction Logic
 * Handles Likes, Comments, and Deletes using Core JS Helpers.
 */

document.addEventListener('DOMContentLoaded', () => {

    // 1. Feature Guard: If communities feature is disabled, remove interactive elements
    if (!Features.isEnabled('enable_communities')) {
        document.querySelectorAll('.btn-like, .add-comment-form, .btn-delete-comment').forEach(el => el.remove());
        return;
    }

    // 2. Toggle Comments Visibility
    document.addEventListener('click', (e) => {
        const toggleBtn = e.target.closest('.toggle-comments-btn');
        if (toggleBtn) {
            const postId = toggleBtn.dataset.postId;
            const section = document.getElementById(`comments-section-${postId}`);
            if (section) {
                section.style.display = section.style.display === 'none' ? 'block' : 'none';
            }
        }
    });

    // 3. Handle Likes
    document.addEventListener('click', async (e) => {
        const btn = e.target.closest('.btn-like');
        if (!btn) return;

        if (!Features.isEnabled('enable_likes')) {
            UI.toast('الإعجابات معطلة حاليًا', 'warning');
            return;
        }

        const postId = btn.dataset.postId;
        const icon = btn.querySelector('i');
        const countSpan = btn.querySelector('.like-count');

        // Optimistic UI update (optional, but good UX)
        // For now, we wait for server to ensure consistency, but disable button
        btn.disabled = true;

        const res = await Http.post(`/communities/post/${postId}/like/`);

        if (res.ok && res.data.success) {
            countSpan.textContent = res.data.count;
            if (res.data.liked) {
                icon.classList.remove('far', 'text-muted');
                icon.classList.add('fas', 'text-danger');
            } else {
                icon.classList.remove('fas', 'text-danger');
                icon.classList.add('far', 'text-muted');
            }
        } else {
            UI.toast(res.error || 'حدث خطأ أثناء تسجيل الإعجاب', 'error');
        }

        btn.disabled = false;
    });

    // 4. Handle Comment Submission
    document.addEventListener('submit', async (e) => {
        if (!e.target.matches('.add-comment-form')) return;

        e.preventDefault();

        if (!Features.isEnabled('enable_comments')) {
            UI.toast('التعليقات معطلة حاليًا', 'warning');
            return;
        }

        const form = e.target;
        const postId = form.dataset.postId;
        const input = form.querySelector('input[name="content"]');
        const submitBtn = form.querySelector('button[type="submit"]');

        UI.showLoading(submitBtn);

        const formData = new FormData(form);
        const res = await Http.post(`/communities/post/${postId}/comment/`, formData);

        if (res.ok && res.data.success) {
            form.reset();
            
            // Hide "no comments" message if exists
            const noComments = document.getElementById(`no-comments-${postId}`);
            if (noComments) noComments.style.display = 'none';

            // Append comment
            const commentsList = document.getElementById(`comments-list-${postId}`);
            if (commentsList) {
                // Create minimal HTML for the new comment
                const newCommentHtml = `
                    <div class="d-flex gap-2 mb-3" id="comment-${res.data.comment.id}">
                        <div class="bg-secondary text-white rounded-circle d-flex align-items-center justify-content-center flex-shrink-0" 
                             style="width: 32px; height: 32px; font-size: 0.8rem;">
                            ${res.data.comment.author.charAt(0).toUpperCase()}
                        </div>
                        <div class="flex-grow-1">
                            <div class="bg-white rounded-3 p-2 px-3">
                                <strong class="small">${res.data.comment.author}</strong>
                                <p class="mb-0 small">${res.data.comment.content}</p>
                            </div>
                            <div class="d-flex gap-3 mt-1 small text-muted">
                                <span>الآن</span>
                                <button class="btn btn-link btn-sm p-0 text-danger btn-delete-comment" 
                                        data-id="${res.data.comment.id}">حذف</button>
                            </div>
                        </div>
                    </div>
                `;
                commentsList.insertAdjacentHTML('beforeend', newCommentHtml);
            }

            // Update count
            const countEl = document.getElementById(`comment-count-${postId}`);
            if (countEl) countEl.textContent = parseInt(countEl.textContent || '0') + 1;

        } else {
            UI.toast(res.error || 'فشل إضافة التعليق', 'error');
        }

        UI.hideLoading(submitBtn);
    });

    // 5. Handle Comment Deletion
    document.addEventListener('click', async (e) => {
        const btn = e.target.closest('.btn-delete-comment');
        if (!btn) return;

        // Optional: Check feature toggle for deletion if separated
        // if (!Features.isEnabled('enable_comment_delete')) return;

        if (!UI.confirm('هل أنت متأكد من حذف هذا التعليق؟')) return;

        const commentId = btn.dataset.id;
        
        // Disable button to prevent double clicks
        btn.disabled = true;

        const res = await Http.post(`/communities/comment/${commentId}/delete/`);

        if (res.ok && res.data.success) {
            const commentEl = document.getElementById(`comment-${commentId}`);
            if (commentEl) {
                // Determine postId to update count
                const commentsSection = commentEl.closest('[id^="comments-section-"]');
                if (commentsSection) {
                    const postId = commentsSection.id.replace('comments-section-', '');
                    const countEl = document.getElementById(`comment-count-${postId}`);
                    if (countEl) countEl.textContent = Math.max(0, parseInt(countEl.textContent || '0') - 1);
                }
                commentEl.remove();
                UI.toast('تم حذف التعليق بنجاح', 'success');
            }
        } else {
            UI.toast(res.error || 'فشل حذف التعليق', 'error');
            btn.disabled = false;
        }
    });

});
