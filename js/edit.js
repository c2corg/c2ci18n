var save_ok = false;
var languages = ['fr', 'it', 'de', 'en', 'es', 'ca', 'eu']

/** easily retrieve selected value of a radio button group */
function $RF(el, radioGroup) {
  if($(el).type && $(el).type.toLowerCase() == 'radio') {
     var radioGroup = $(el).name;
     var el = $(el).form;
  }
  else if ($(el).tagName.toLowerCase() != 'form') {
    return false;
  }
  var checked = $(el).getInputs('radio', radioGroup).find(
    function(re) { return re.checked; }
  );
  return (checked) ? $F(checked) : null;
}

/** If user tries to quit page with unsaved changes, ask if the chanegs should really be discarded */
Event.observe(window, 'unload', function() {
  if (!save_ok) return false;

  r = confirm('You have unsaved changes.\nDo you want to save them before leaving this page?');
  if (r == true) {
    /*save_translation();*/
    $('edit_form').submit();
  }
});

/** textarea changes: new changes to potentially save */
$$('textarea').each(
  function(item) {
    Event.observe(item, 'change', function() { save_ok = true; });
  }
);

/** radio buttons changes: update textarea color */
$$('input').each(
  function(item) {
    if (item.type && item.type.toLowerCase() == 'radio') {
      Event.observe(item, 'change', function() {
        save_ok = true
        new_class = $F(item);
        textarea = $(item.name.substr(0, 2));
        textarea.classNames().each( function(cl) { textarea.removeClassName(cl) } );
        $(item.name.substr(0, 2)).addClassName(new_class);
      });
    }
  }
);
