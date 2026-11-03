// Runs before first paint (not deferred) so the page never flashes the wrong theme.
// Saved choice wins; otherwise follow the device's dark/light setting.
(function(){
  var t=null;
  try{t=localStorage.getItem('cc_theme');}catch(e){}
  if(t!=='dark'&&t!=='light'){t=(window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches)?'dark':'light';}
  document.documentElement.setAttribute('data-theme',t);
})();
