# Game classes
import BigWorld
from debug_utils import LOG_WARNING
from Avatar import PlayerAvatar
from VehicleGunRotator import VehicleGunRotator
from AvatarInputHandler import AvatarInputHandler 
import aih_constants
import Keys
import math

# GUIFlash
from gambiter import g_guiFlash
from gambiter.flash import COMPONENT_TYPE

# ModSettingsAPI
from gui.modsSettingsApi import g_modsSettingsApi, templates

# Modes in which we have to be in order to reduce our reticle size
# Arcade = Regular third person
# Strategic = Topdown arty view
# Sniper = Regular sniper mode
# Dual gun = Tanks with two guns are always in this mode
whitelisted_modes = (aih_constants.CTRL_MODE_NAME.ARCADE, aih_constants.CTRL_MODE_NAME.STRATEGIC, aih_constants.CTRL_MODE_NAME.SNIPER, aih_constants.CTRL_MODE_NAME.DUAL_GUN)

modID = 'archie_TrueServerReticle'
modVersion = 5
settingsTemplate = {
	"modDisplayName": "True Server Reticle",
	"enabled": True,
	"column1": [
		templates.createCheckbox("Show gun dispersion", 
			"showDispersionNumber", 
			True, 
			tooltip="{HEADER}Show dispersion number{/HEADER}{BODY}Shows the current gun dispersion as a number just below the crosshair.{/BODY}"),
		templates.createCheckbox("Enable gun rotation fix", 
			"gunRotationFix", 
			True, 
			tooltip="{HEADER}Enable gun rotation fix{/HEADER}{BODY}Fixes gun rotation being desynced from the server even if using server reticle.\nThis may cause animations to become jerky or stuttery.\nDoesn't work if the \"Enable Server Reticle\" setting is off!{/BODY}"),
		templates.createCheckbox("Enable reticle scaling", 
			"reticleScaling", 
			True, 
			tooltip="{HEADER}Enable reticle scaling{/HEADER}{BODY}Scales the reticle down to its true size according to shot distribution.\nThis leads to the reticle being smaller, but shots may now hit its very edge.{/BODY}"),
		templates.createDropdown("Reticle scaling type", 
			"scalingType",
			["Linear", "Interpolated"],
			0,
			tooltip="{HEADER}Reticle scaling type{/HEADER}{BODY}Controls how the reticle is scaled.\nLinear scaling is best suited for low-latency stable internet connections.\nInterpolated scaling prevents shots going outside of the reticle on unstable internet,\n while giving an impression of faster aiming time.{/BODY}"),
		templates.createCheckbox("Show aiming time", 
			"showAimTime",
			True,
			tooltip="{HEADER}Show aiming time{/HEADER}{BODY}Shows the current remaining aimtime just below the crosshair.{/BODY}"),
		
	]
}

settings = {
	"enabled": True,
	"showDispersionNumber": True,
	"gunRotationFix": True,
	"reticleScaling": True,
	"scalingType": 0,
	"showAimTime": False
}

easing_factor = 1

def detour_function(old, new):
	def run(*args, **kwargs):
		return new(old, *args, **kwargs)

	return run

def draw_text(id, x, y, text, scale, visible):
	global COMPONENT_TYPE
	global g_guiFlash
	g_guiFlash.deleteComponent(id)
	g_guiFlash.createComponent(id, COMPONENT_TYPE.LABEL, {'text': text, 'alignX': 'center', 'x': x, 'y': y, 'scaleX': scale, 'scaleY': scale, 'visible': visible})

# Called when the dispersion is changed
def PlayerAvatar_GetShotAngle(original, self, turretRotationSpeed, withShot = 0):
	global settings
	global easing_factor
	result = original(self, turretRotationSpeed, withShot)

	screen_height = BigWorld.screenHeight()
	current_dispersion = result[0] * 100 # result[1] would be current client-side dispersion
	real_dispersion = current_dispersion / 1.71 if (settings["reticleScaling"] and (settings["scalingType"] == 0)) else current_dispersion

	easing_factor = 1

	# Use interpolation
	aiming_start_time = self._PlayerAvatar__aimingInfo[0]
	aiming_start_factor = self._PlayerAvatar__aimingInfo[1]
	mult_factor = self._PlayerAvatar__dispersionInfo[0]
	total_aiming_time = self._PlayerAvatar__dispersionInfo[4]
	aiming_time_remaining = max(aiming_start_time + (total_aiming_time * math.log(aiming_start_factor / mult_factor)) - BigWorld.time(), 0)

	if settings["scalingType"] == 1 and settings["reticleScaling"]:
		fully_aimed_dispersion = current_dispersion * math.exp((-aiming_time_remaining) / total_aiming_time)

		# Dispersion is not altered if aim time remaining > 2 seconds
		easing_factor = 1 - ease_aiming(min(aiming_time_remaining / 4.5, 1)) 
		# draw_text("easing_factor", 0, round(screen_height * 0.62), ("easing_factor: {:.3f} aimtime: {:.3f}").format(easing_factor, aiming_time_remaining), 1.75, (settings["scalingType"] == 1 and settings["reticleScaling"] and settings["enabled"]))

		real_dispersion = current_dispersion / max((1.71 * easing_factor, 1))

	text = ""
	if settings["showDispersionNumber"] and settings["showAimTime"]:
		text = "{:.3f} ({:.1f}s)".format(real_dispersion, aiming_time_remaining)
	elif settings["showDispersionNumber"]:
		text = "{:.3f}".format(real_dispersion)
	elif settings["showAimTime"]:
		text = "{:.1f}s".format(aiming_time_remaining) 

	draw_text("GunInformationText", 0, round(screen_height * 0.52), text, 1.75, (settings["enabled"] and (settings["showDispersionNumber"] or settings["showAimTime"])))

	return result

def ease_aiming(x):
	  return 1 - math.cos((x * math.pi) / 2);

# Updates the crosshair's attributes when not using server reticle
def AvatarInputHandler_UpdateClientGunMarker(original, self, pos, direction, size, relaxTime, collData):
	global settings
	global easing_factor
	if (self._AvatarInputHandler__ctrlModeName in whitelisted_modes) and settings["enabled"] and settings["reticleScaling"]:
		size = tuple(x / max((1.71 * easing_factor, 1)) for x in size)
	return original(self, pos, direction, size, relaxTime, collData)

# Updates the crosshair's attributes when using server reticle
def AvatarInputHandler_UpdateServerGunMarker(original, self, pos, direction, size, relaxTime, collData):
	global settings
	global easing_factor
	if (self._AvatarInputHandler__ctrlModeName in whitelisted_modes) and settings["enabled"] and settings["reticleScaling"]:
		size = tuple(x / max((1.71 * easing_factor, 1)) for x in size)
	return original(self, pos, direction, size, relaxTime, collData)

# Updates the crosshair's attributes when using dual guns?
def AvatarInputHandler_UpdateDualAccGunMarker(original, self, pos, direction, size, relaxTime, collData):
	global settings
	global easing_factor
	if (self._AvatarInputHandler__ctrlModeName in whitelisted_modes) and settings["enabled"] and settings["reticleScaling"]:
		size = tuple(x / max((1.71 * easing_factor, 1)) for x in size)
	return original(self, pos, direction, size, relaxTime, collData)

# Controls turret rotation and where the shot goes
def VehicleGunRotator_setShotPosition(original, self, vehicleID, shotPos, shotVec, dispersionAngle, forceValueRefresh=False):
	global settings
	if self._avatar.vehicle and settings["gunRotationFix"] and settings["enabled"]:
		self._VehicleGunRotator__turretYaw, self._VehicleGunRotator__gunPitch = self._avatar.vehicle.getServerGunAngles()
		forceValueRefresh = True
	return original(self, vehicleID, shotPos, shotVec, dispersionAngle, forceValueRefresh)

def onSettingsChanged(id, new_settings):
	global settings
	if id == modID:
		LOG_WARNING("[TSR by Archie] Applying settings {}".format(new_settings))
		settings = new_settings

def init():
	# Create hooks
	PlayerAvatar.getOwnVehicleShotDispersionAngle = detour_function(PlayerAvatar.getOwnVehicleShotDispersionAngle, PlayerAvatar_GetShotAngle)
	VehicleGunRotator.setShotPosition = detour_function(VehicleGunRotator.setShotPosition, VehicleGunRotator_setShotPosition)
	AvatarInputHandler.updateClientGunMarker = detour_function(AvatarInputHandler.updateClientGunMarker, AvatarInputHandler_UpdateClientGunMarker)
	AvatarInputHandler.updateServerGunMarker = detour_function(AvatarInputHandler.updateServerGunMarker, AvatarInputHandler_UpdateServerGunMarker)
	AvatarInputHandler.updateDualAccGunMarker = detour_function(AvatarInputHandler.updateDualAccGunMarker, AvatarInputHandler_UpdateDualAccGunMarker)
	# Register settings
	# def getModSettings(linkage, template=None)
	global settings
	global settingsTemplate
	savedSettings = g_modsSettingsApi.getModSettings(modID, settingsTemplate)
	if savedSettings:
		LOG_WARNING("[TSR by Archie] Loading saved settings {}".format(savedSettings))
		settings = savedSettings
		# def registerCallback(linkage, callback, buttonHandler = None)
		g_modsSettingsApi.registerCallback(modID, onSettingsChanged)
	else:
		# def setModTemplate(linkage, template, callback, buttonHandler = None)
		settings = g_modsSettingsApi.setModTemplate(modID, settingsTemplate, onSettingsChanged)
	LOG_WARNING("[TSR by Archie] Loaded successfully.")

def fini():
	LOG_WARNING("[TSR by Archie] Mod is shutting down!")