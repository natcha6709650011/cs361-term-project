(function () {
    const MAX = 5 * 1024 * 1024, TYPES = ["image/jpeg", "image/png", "image/webp"];
    let file = null, blobUrl = null;
    const $ = (id) => document.getElementById(id);
    const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  
    const style = document.createElement("style");
    style.textContent = `
  .img-field { display: grid; gap: 6px; font-weight: 700; }
  .img-drop { position: relative; display: grid; place-items: center; min-height: 140px; border: 2px dashed #c9d0da; border-radius: 14px; background: #f8f9fb; cursor: pointer; overflow: hidden; text-align: center; }
  .img-drop:hover, .img-drop:focus-visible, .img-drop.is-over { border-color: #c60039; background: #fff5f7; outline: 0; }
  .img-drop img { display: block; width: 100%; max-height: 240px; object-fit: cover; }
  .img-drop img[hidden] { display: none; }
  .img-drop__hint { padding: 10px 14px; color: #5b6579; font-weight: 600; font-size: 14px; }
  .img-drop img:not([hidden]) + .img-drop__hint { position: absolute; inset: auto 0 0 0; background: rgb(23 32 51 / 65%); color: #fff; }
  #imgMsg.is-error { color: #c60039; }`;
    document.head.appendChild(style);
    ["dragover", "drop"].forEach((t) => window.addEventListener(t, (e) => e.preventDefault()));
  
    function html(url) {
      file = null;
      return `<div class="img-field"><span>รูปภาพ</span>
        <div class="img-drop" id="imgDrop" tabindex="0" role="button" aria-label="เลือกหรือวางไฟล์รูปภาพ">
          <img id="imgPrev" alt="ตัวอย่างรูปห้อง" ${url ? `src="${esc(url)}"` : "hidden"} />
          <div class="img-drop__hint">${url ? "ลากไฟล์รูปใหม่มาวาง หรือคลิกเพื่อเปลี่ยนรูป" : "ลากไฟล์รูปมาวางที่นี่ หรือคลิกเพื่อเลือกไฟล์"}</div>
        </div>
        <input type="file" id="imgFile" accept="image/jpeg,image/png,image/webp" hidden />
        <small id="imgMsg">รองรับ JPG, PNG, WebP ขนาดไม่เกิน 5 MB</small></div>`;
    }
  
    function pick(f) {
      const msg = $("imgMsg");
      msg.classList.remove("is-error");
      if (!TYPES.includes(f.type)) { msg.textContent = "รองรับเฉพาะไฟล์ JPG, PNG, WebP"; msg.classList.add("is-error"); return; }
      if (f.size > MAX) { msg.textContent = "ไฟล์ใหญ่เกิน 5 MB"; msg.classList.add("is-error"); return; }
      file = f;
      if (blobUrl) URL.revokeObjectURL(blobUrl);
      blobUrl = URL.createObjectURL(f);
      $("imgPrev").src = blobUrl; $("imgPrev").hidden = false;
      msg.textContent = `เลือกไฟล์ใหม่: ${f.name} (จะอัปโหลดเมื่อกดบันทึก)`;
    }
  
    function bind() {
      const drop = $("imgDrop"), input = $("imgFile");
      drop.addEventListener("click", () => input.click());
      drop.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); input.click(); } });
      input.addEventListener("change", () => input.files[0] && pick(input.files[0]));
      ["dragenter", "dragover"].forEach((t) => drop.addEventListener(t, (e) => { e.preventDefault(); drop.classList.add("is-over"); }));
      ["dragleave", "drop"].forEach((t) => drop.addEventListener(t, (e) => { e.preventDefault(); drop.classList.remove("is-over"); }));
      drop.addEventListener("drop", (e) => { const f = e.dataTransfer.files[0]; if (f) pick(f); });
    }
  
    async function upload(roomId, api, base) {
      const info = await api(`${base}/rooms/${roomId}/image-upload`, { method: "POST", body: JSON.stringify({ content_type: file.type, size: file.size }) });
      const fd = new FormData();
      Object.entries(info.fields).forEach(([k, v]) => fd.append(k, v));
      fd.append("file", file); 
      const res = await fetch(info.upload_url, { method: "POST", body: fd });
      if (!res.ok) throw new Error("อัปโหลดรูปไม่สำเร็จ");
      return info.image_url;
    }
  
    window.RoomImageField = { html, bind, upload, changed: () => !!file };
  })();