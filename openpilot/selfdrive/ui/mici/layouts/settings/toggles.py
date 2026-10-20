from collections.abc import Callable

from openpilot.cereal import log

from openpilot.system.ui.widgets.scroller import NavScroller
from openpilot.selfdrive.ui.mici.widgets.button import BigParamControl, BigMultiParamToggle, BigMultiToggle, BigToggle, GreyBigButton
from openpilot.selfdrive.ui.mici.widgets.dialog import BigConfirmationCircleButton
from openpilot.system.ui.lib.application import gui_app
from openpilot.selfdrive.ui.layouts.settings.common import restart_needed_callback
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.common import zss_flags

PERSONALITY_TO_INT = log.LongitudinalPersonality.schema.enumerants

# op0.11.2-zss: DIY eGPU power limit, tap to cycle. Stored in /data/personal_settings/EgpuPowerLimitW,
# read by modeld when it starts (next drive).
EGPU_POWER_LABELS = ["40 W", "60 W", "80 W"]
EGPU_POWER_VALUES = ["40", "60", "80"]
EGPU_POWER_DEFAULT = "60"


class EgpuPowerToggle(BigMultiToggle):
  def __init__(self):
    super().__init__("eGPU power", EGPU_POWER_LABELS, select_callback=self._on_select)
    self.load()

  def load(self):
    value = zss_flags.get_str(zss_flags.EGPU_POWER_LIMIT, EGPU_POWER_DEFAULT)
    if value not in EGPU_POWER_VALUES:  # e.g. an old "0" (full): reset so UI and modeld agree
      value = EGPU_POWER_DEFAULT
      zss_flags.put_str(zss_flags.EGPU_POWER_LIMIT, value)
    self.set_value(EGPU_POWER_LABELS[EGPU_POWER_VALUES.index(value)])

  def _on_select(self, label: str):
    zss_flags.put_str(zss_flags.EGPU_POWER_LIMIT, EGPU_POWER_VALUES[EGPU_POWER_LABELS.index(label)])


class ExperimentalModeConfirmPage(NavScroller):
  def __init__(self, on_confirm: Callable[[], None]):
    super().__init__()

    accept = BigConfirmationCircleButton("enable\nexperimental mode",
                                         gui_app.texture("icons_mici/setup/driver_monitoring/dm_check.png", 64, 64),
                                         lambda: self.dismiss(on_confirm))

    self._scroller.add_widgets([
      GreyBigButton("enabling\nexperimental mode", "scroll to continue",
                    gui_app.texture("icons_mici/setup/warning.png", 64, 64)),
      GreyBigButton("", "openpilot defaults to driving in chill mode."),
      GreyBigButton("", "Experimental mode enables alpha-level features that aren't ready for chill mode."),
      GreyBigButton("End-to-End Longitudinal Control"),
      GreyBigButton("", "Let the driving model control the gas and brakes."),
      GreyBigButton("", "openpilot will drive as it thinks a human would, including stopping for red lights and stop signs."),
      GreyBigButton("", "The set speed will only act as an upper bound."),
      GreyBigButton("", "This is an alpha quality feature; mistakes should be expected."),
      GreyBigButton("New Driving Visualization"),
      GreyBigButton("", "The path will change colors to communicate acceleration intent."),
      GreyBigButton("", "Red for braking, green for acceleration, and gray for coasting."),
      accept,
    ])


class TogglesLayoutMici(NavScroller):
  def __init__(self):
    super().__init__()

    self._personality_toggle = BigMultiParamToggle("driving personality", "LongitudinalPersonality", ["aggressive", "standard", "relaxed"])
    self._experimental_btn = BigToggle("experimental mode", initial_state=ui_state.params.get_bool("ExperimentalMode"),
                                       toggle_callback=self._on_experimental_mode)
    is_metric_toggle = BigParamControl("use metric units", "IsMetric")
    ldw_toggle = BigParamControl("lane departure warnings", "IsLdwEnabled")
    # op0.11.2-zss: Adaptive Experimental Mode, default ON (stored in /data/personal_settings, not Params)
    self._aem_toggle = BigToggle("adaptive experimental (AEM)",
                                 initial_state=zss_flags.get_bool(zss_flags.AEM_ENABLED, default=True),
                                 toggle_callback=lambda state: zss_flags.put_bool(zss_flags.AEM_ENABLED, state))
    # op0.11.2-zss: blinker lane change on/off, default OFF (stored in /data/personal_settings, not Params)
    self._lane_change_toggle = BigToggle("blinker lane change",
                                         initial_state=zss_flags.get_bool(zss_flags.LANE_CHANGE_ENABLED),
                                         toggle_callback=lambda state: zss_flags.put_bool(zss_flags.LANE_CHANGE_ENABLED, state))
    self._egpu_power_toggle = EgpuPowerToggle()  # op0.11.2-zss
    always_on_dm_toggle = BigParamControl("always-on driver monitor", "AlwaysOnDM")
    record_front = BigParamControl("record & upload cabin camera", "RecordFront", toggle_callback=restart_needed_callback)
    record_mic = BigParamControl("record & upload mic audio", "RecordAudio", toggle_callback=restart_needed_callback)
    enable_openpilot = BigParamControl("enable openpilot", "OpenpilotEnabledToggle", toggle_callback=restart_needed_callback)

    self._scroller.add_widgets([
      self._personality_toggle,
      self._experimental_btn,
      self._aem_toggle,
      is_metric_toggle,
      ldw_toggle,
      self._lane_change_toggle,
      self._egpu_power_toggle,
      always_on_dm_toggle,
      record_front,
      record_mic,
      enable_openpilot,
    ])

    # Toggle lists
    self._refresh_toggles = (
      ("ExperimentalMode", self._experimental_btn),
      ("IsMetric", is_metric_toggle),
      ("IsLdwEnabled", ldw_toggle),
      ("AlwaysOnDM", always_on_dm_toggle),
      ("RecordFront", record_front),
      ("RecordAudio", record_mic),
      ("OpenpilotEnabledToggle", enable_openpilot),
    )

    enable_openpilot.set_enabled(lambda: not ui_state.engaged)
    record_front.set_enabled(False if ui_state.params.get_bool("RecordFrontLock") else (lambda: not ui_state.engaged))
    record_mic.set_enabled(lambda: not ui_state.engaged)
    self._lane_change_toggle.set_enabled(lambda: not ui_state.engaged)  # op0.11.2-zss: no change while engaged
    self._aem_toggle.set_enabled(lambda: not ui_state.engaged)          # op0.11.2-zss: no change while engaged
    self._egpu_power_toggle.set_enabled(lambda: not ui_state.engaged)   # op0.11.2-zss: used from the next drive

    if ui_state.params.get_bool("ShowDebugInfo"):
      gui_app.set_show_touches(True)
      gui_app.set_show_fps(True)

    ui_state.add_engaged_transition_callback(self._update_toggles)

  def _update_state(self):
    super()._update_state()

    if ui_state.sm.updated["selfdriveState"]:
      personality = PERSONALITY_TO_INT[ui_state.sm["selfdriveState"].personality]
      if personality != ui_state.personality and ui_state.started:
        self._personality_toggle.set_value(self._personality_toggle._options[personality])
      ui_state.personality = personality

  def show_event(self):
    super().show_event()
    self._update_toggles()

  def _update_toggles(self):
    ui_state.update_params()

    # CP gating for experimental mode
    if ui_state.CP is not None:
      if ui_state.has_longitudinal_control:
        self._experimental_btn.set_visible(True)
        self._personality_toggle.set_visible(True)
        self._aem_toggle.set_visible(True)
      else:
        # no long for now
        self._experimental_btn.set_visible(False)
        self._experimental_btn.set_checked(False)
        self._personality_toggle.set_visible(False)
        self._aem_toggle.set_visible(False)
        ui_state.params.remove("ExperimentalMode")

    # Refresh toggles from params to mirror external changes
    for key, item in self._refresh_toggles:
      item.set_checked(ui_state.params.get_bool(key))
    self._lane_change_toggle.set_checked(zss_flags.get_bool(zss_flags.LANE_CHANGE_ENABLED))  # op0.11.2-zss
    self._aem_toggle.set_checked(zss_flags.get_bool(zss_flags.AEM_ENABLED, default=True))   # op0.11.2-zss
    self._egpu_power_toggle.load()                                                          # op0.11.2-zss

  def _on_experimental_mode(self, state: bool):
    if state and not ui_state.params.get_bool("ExperimentalModeConfirmed"):
      # Don't show enabled state until confirm
      self._experimental_btn.set_checked(False)

      def on_confirm():
        ui_state.params.put_bool("ExperimentalModeConfirmed", True)
        ui_state.params.put_bool("ExperimentalMode", True)
        self._experimental_btn.set_checked(True)

      gui_app.push_widget(ExperimentalModeConfirmPage(on_confirm))
    else:
      ui_state.params.put_bool("ExperimentalMode", state)
