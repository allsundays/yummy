var host = 'http://yummy.allsunday.in',
    api_prefix = host + '/api/v1';

$('#jsVisit').on('click', function(e) {
  e.preventDefault();
  chrome.tabs.create({
    url: host + '/'
  });
});

$('#jsAdd').on('click', function(e) {
  e.preventDefault();
  var sk = $.cookie('sk');
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
      url: api_prefix + '/add',
      data: {
        url: url,
        sk: sk
      }
    }).done(function(resp) {
      console.log(resp);
    }).fail(function(resp) {
      console.log(resp);
    });

  });
});


$('#jsLogin').on('submit', function(e) {
  e.preventDefault();
  $.ajax({
    type: 'POST',
    url: api_prefix + '/login',
    data: $(this).serialize()
  }).done(function(resp) {
    var sk = resp.data;
    $.cookie('sk', sk);
    alert('ok');
  });
});


(function() {
  var sk = $.cookie('sk');
  if (sk) {
    $('#jsLogin').hide();
  }
})()
