function loadframe(url, id) {
    const el = document.getElementById(id);
    ( fetch(url)).then((response)=>{
      return response.text();
    })
    .then((html)=>{
      el.innerHTML=html;
    })
  }