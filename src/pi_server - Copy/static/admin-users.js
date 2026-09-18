const {csrfToken} = window.adminUsersConfig;
const form = document.querySelector("#new-user");
const message = document.querySelector("#message");
const list = document.querySelector("#users");

form.addEventListener("submit", async event => {
  event.preventDefault();
  const response = await fetch("/api/admin/users", {
    method: "POST",
    headers: {"Content-Type": "application/json", "X-CSRF-Token": csrfToken},
    body: JSON.stringify(Object.fromEntries(new FormData(form))),
  });
  const data = await response.json();
  message.textContent = data.message || "Đã tạo tài khoản.";
  message.className = response.ok ? "notice" : "notice error";
  if (!response.ok) return;

  form.reset();
  const row = document.createElement("article");
  row.className = "user";
  row.innerHTML = '<span class="avatar icon">person</span><div><div class="user-name"></div><span class="role">user</span></div><time class="created"></time>';
  row.querySelector(".user-name").textContent = data.user.username;
  row.querySelector("time").textContent = data.user.created_at;
  list.append(row);
  document.querySelector("#count").textContent = `${list.children.length} tài khoản`;
});
