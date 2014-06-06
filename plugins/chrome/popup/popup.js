var host = 'http://www.allsunday.in:8888';

$('#jsVisit').on('click', function(e) {
  e.preventDefault();
  chrome.tabs.create({
    url: host + '/'
  });
});

$('#jsAdd').on('click', function(e) {
  e.preventDefault();
  chrome.tabs.query({
    active: true,
    currentWindow: true
  }, function(tabs) {
    if (!tabs.length) {
      return;
    }

    var url = tabs[0].url;
    $.ajax({
      type: 'POST',
      url: host + '/add',
      data: {
        url: url,
        user: 'gfreezy'
      }
    }).done(function(resp) {
      console.log(resp);
    }).fail(function(resp) {
      console.log(resp);
    });

  });
});
