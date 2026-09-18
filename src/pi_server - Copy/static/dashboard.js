const config = window.dashboardConfig;
const $ = selector => document.querySelector(selector);

async function request(url, options) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || "Yêu cầu thất bại");
  return data;
}

function updateStatus(data) {
  $("#face-count").textContent = data.faces;
  $("#fps").textContent = data.fps;
  $("#confidence").textContent = data.confidence ? `${Math.round(data.confidence * 100)}%` : "—";
  $("#match-name").textContent = data.match ? data.name : data.faces ? "Đang xác minh" : "Không có";
  $("#match-name").className = data.match ? "match" : "unknown";
  $("#system-message").textContent = data.ready ? "Nhận diện đang hoạt động." : "Camera hoặc mô hình chưa sẵn sàng.";
  $("#system-pill").className = `system-pill ${data.ready ? "online" : "offline"}`;
  $("#system-label").textContent = data.ready ? "Hệ thống sẵn sàng" : "Camera chưa sẵn sàng";

  const door = data.door;
  const online = door.enabled && door.connected && door.online;
  const labels = {closed: "Cửa đóng", opening: "Đang mở khóa", open: "Cửa mở", closing: "Đang khóa", error: "Lỗi khóa", unknown: "Chưa rõ"};
  $("#door-state").textContent = online ? labels[door.status] || "Chưa rõ" : "Mất kết nối";
  $("#door-state").className = `door-pill ${online ? "online" : "offline"}`;
  $("#door-icon").textContent = door.status === "open" ? "door_open" : "door_front";
  document.querySelectorAll("[data-door-action]").forEach(button => button.disabled = !online);
}

async function pollStatus() {
  try {
    updateStatus(await request("/status"));
  } catch (_) {
    $("#system-pill").className = "system-pill offline";
    $("#system-label").textContent = "Server mất kết nối";
  }
}

document.querySelectorAll("[data-door-action]").forEach(button => {
  button.addEventListener("click", async () => {
    button.disabled = true;
    try {
      const data = await request("/api/door/command", {
        method: "POST",
        headers: {"Content-Type": "application/json", "X-CSRF-Token": config.csrfToken},
        body: JSON.stringify({action: button.dataset.doorAction}),
      });
      $("#door-message").textContent = data.message;
    } catch (error) {
      $("#door-message").textContent = error.message;
    } finally {
      setTimeout(pollStatus, 800);
    }
  });
});

async function loadPeople() {
  const data = await request("/get_people");
  const rows = data.people.map(person => {
    const row = document.createElement("div");
    row.className = "person";
    const icon = document.createElement("span");
    icon.className = "avatar icon";
    icon.textContent = "person";
    const text = document.createElement("div");
    const name = document.createElement("div");
    name.className = "person-name";
    name.textContent = person.name;
    const count = document.createElement("div");
    count.className = "person-count";
    count.textContent = `${person.count} mẫu khuôn mặt`;
    const remove = document.createElement("button");
    remove.type = "button";
    remove.title = `Xóa ${person.name}`;
    remove.innerHTML = '<span class="icon">delete</span>';
    remove.addEventListener("click", () => removePerson(person.name));
    text.append(name, count);
    row.append(icon, text, remove);
    return row;
  });
  $("#people").replaceChildren(...rows);
}

async function removePerson(name) {
  if (!confirm(`Xóa ${name}?`)) return;
  try {
    const data = await request("/delete_person", {
      method: "POST",
      headers: {"Content-Type": "application/json", "X-CSRF-Token": config.csrfToken},
      body: JSON.stringify({name}),
    });
    $("#enroll-message").textContent = data.message;
    await loadPeople();
  } catch (error) {
    $("#enroll-message").textContent = error.message;
  }
}

if (config.isAdmin) {
  $("#enroll-form").addEventListener("submit", async event => {
    event.preventDefault();
    const name = $("#enroll-name").value.trim();
    try {
      const data = await request("/enroll_web", {
        method: "POST",
        headers: {"Content-Type": "application/json", "X-CSRF-Token": config.csrfToken},
        body: JSON.stringify({name}),
      });
      $("#enroll-message").textContent = data.message;
      event.target.reset();
      await loadPeople();
    } catch (error) {
      $("#enroll-message").textContent = error.message;
    }
  });
  loadPeople().catch(() => {});
}

request("/info").then(data => {
  $("#camera-id").textContent = data.camera === null ? "CAM TCP" : `CAM-${String(data.camera).padStart(2, "0")}`;
}).catch(() => {});
pollStatus();
setInterval(pollStatus, 1000);
