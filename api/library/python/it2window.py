#!/usr/bin/python
# This is python 2.7 on macOS 10.12.

from __future__ import print_function

from it2global import get_socket, wait
import it2session
import it2socket
import api_pb2
import it2tab

class AbstractWindow(object):
  def __repr__(self):
    raise NotImplementedError("unimplemented")

  def get_window_id(self):
    raise NotImplementedError("unimplemented")

  def get_tabs(self):
    raise NotImplementedError("unimplemented")

  def create_tab(self, profile=None, command=None, index=None):
    raise NotImplementedError("unimplemented")


class FutureWindow(AbstractWindow):
  def __init__(self, future):
    self.future = future
    self.window = None
    self.status = None

  def __repr__(self):
    return "<FutureWindow status=%s window=%s>" % (str(self.get_status()), repr(self._get_window()))

  def get_window_id(self):
    return self._get_window().get_window_id()

  def get_tabs(self):
    return self._get_window().get_tabs()

  def create_tab(self, profile=None, command=None, index=None):
    if self.future is None:
      return self._get_window().create_tab(profile=profile, command=command, index=index)

    def create_inner(response):
      return get_socket().request_create_tab(
          profile=profile, window=self.get_window_id(), index=index, command=command)
    createTabFuture = it2socket.DependentFuture(self.future, create_inner)
    return it2tab.FutureTab(createTabFuture);

  def get_status(self):
    self._parse_if_needed()
    return self.status

  def _get_window(self):
    self._parse_if_needed()
    return self.window

  def _parse_if_needed(self):
    if self.future is not None:
      self._parse(self.future.get())
      self.future = None

  def _parse(self, response):
    self.status = response.status
    if self.status == api_pb2.CreateTabResponse.OK:
      session = it2session.Session(response.session_id)
      tab = it2tab.Tab(response.tab_id, [ session ])
      self.window = Window(response.window_id, [ tab ])

class Window(AbstractWindow):
  def __init__(self, window_id, tabs):
    self.window_id = window_id
    self.tabs = tabs

  def __repr__(self):
    return "<Window id=%s tabs=%s>" % (self.window_id, self.tabs)

  def get_window_id(self):
    return self.window_id

  def get_tabs(self):
    return self.tabs

  def create_tab(self, profile=None, command=None, index=None):
    return it2tab.FutureTab(get_socket().request_create_tab(
      profile=profile, window=self.window_id, index=index, command=command))

