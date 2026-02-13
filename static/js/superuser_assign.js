// superuser_assign.js
// Drag-and-drop assignment UI for SB Admin

document.addEventListener('DOMContentLoaded', function() {
  const usersList = document.getElementById('users-list');
  const sitesList = document.getElementById('sites-list');
  const assignments = JSON.parse(document.getElementById('assignments-data').textContent);
  const users = JSON.parse(document.getElementById('users-data').textContent);
  const sites = JSON.parse(document.getElementById('sites-data').textContent);

  // Render users and sites
  usersList.innerHTML = users.map(u => `<li class="list-group-item user-draggable" draggable="true" data-user-id="${u.id}">${u.username}</li>`).join('');
  sitesList.innerHTML = sites.map(s => `
    <div class="card mb-2">
      <div class="card-header">${s.name}</div>
      <ul class="list-group list-group-flush" id="site-users-${s.id}"></ul>
    </div>
  `).join('');

  // Fill assigned users
  assignments.forEach(a => {
    const user = users.find(u => u.id === a.user_id);
    if (user) {
      const ul = document.getElementById(`site-users-${a.site_id}`);
      if (ul) {
        ul.innerHTML += `<li class="list-group-item assigned-user" data-user-id="${user.id}">${user.username} <button class="btn btn-sm btn-danger float-right unassign-btn">Remove</button></li>`;
      }
    }
  });

  // Drag-and-drop logic
  let draggedUser = null;
  usersList.addEventListener('dragstart', function(e) {
    if (e.target.classList.contains('user-draggable')) {
      draggedUser = e.target;
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', draggedUser.getAttribute('data-user-id'));
    }
  });
  document.querySelectorAll('[id^=site-users-]').forEach(ul => {
    ul.addEventListener('dragover', function(e) {
      e.preventDefault();
    });
    ul.addEventListener('drop', function(e) {
      e.preventDefault();
      if (draggedUser) {
        const userId = draggedUser.getAttribute('data-user-id');
        const siteId = this.id.replace('site-users-', '');
        // AJAX assign
        fetch('/core/superuser-admin/assign/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.CSRF_TOKEN },
          body: JSON.stringify({ user_id: userId, site_id: siteId })
        }).then(resp => resp.json()).then(data => {
          if (data.success) {
            this.innerHTML += `<li class=\"list-group-item assigned-user\" data-user-id=\"${userId}\">${draggedUser.textContent} <button class=\"btn btn-sm btn-danger float-right unassign-btn\">Remove</button></li>`;
            draggedUser.remove();
          }
        });
      }
    });
  });
  // Unassign logic
  document.addEventListener('click', function(e) {
    if (e.target.classList.contains('unassign-btn')) {
      const li = e.target.closest('li[data-user-id]');
      const userId = li.getAttribute('data-user-id');
      const siteId = li.closest('ul').id.replace('site-users-', '');
      fetch('/core/superuser-admin/assign/', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.CSRF_TOKEN },
        body: JSON.stringify({ user_id: userId, site_id: siteId })
      }).then(resp => resp.json()).then(data => {
        if (data.success) {
          li.remove();
        }
      });
    }
  });
});
