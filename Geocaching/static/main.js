function loadframe(url, id) {
  const el = document.getElementById(id);
  ( fetch(url)).then((response)=>{
    return response.text();
  })
  .then((html)=>{
    el.innerHTML=html;
  })
}

/**
 * Given a param key it returns its value. If the param does not exists, it returns null.
 * @param {string} key 
 * @returns {string} parameter value
 */
function getUrlParam(key) {
const queryText = window.location.search;
const params = new URLSearchParams(queryText);
if(!params) return null;
return params.get(key) ?? null;
}