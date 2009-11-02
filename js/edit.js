var warning_changes = false;
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

/** If user tries to quit page with unsaved changes, ask if the changes should really be discarded */
function check_changes() {
  if (!warning_changes) return true;

  r = confirm('You have unsaved changes.\nClick \'Ok\' if you want to save them before leaving the page');
  if (r) {
    // save translation before going to quit page
    warning_changes = false;
    $('edit_form').submit();
  }
};

/** watch for changes to the form */
new Form.Observer('edit_form', 0.3, function() { warning_changes = true; });

/** radio buttons changes: update textarea color */
$$('input').each(
  function(item) {
    if (item.type && item.type.toLowerCase() == 'radio') {
      Event.observe(item, 'change', function() {
        new_class = $F(item);
        textarea = $(item.name.substr(0, 2));
        textarea.classNames().each( function(cl) { textarea.removeClassName(cl) } );
        $(item.name.substr(0, 2)).addClassName(new_class);
      });
    }
  }
);
