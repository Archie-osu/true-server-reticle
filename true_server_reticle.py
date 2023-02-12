# Game classes
import BigWorld
from debug_utils import LOG_WARNING
from Avatar import PlayerAvatar
from VehicleGunRotator import VehicleGunRotator
from AvatarInputHandler import AvatarInputHandler 
import aih_constants
import Keys

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
modVersion = 1
settingsTemplate = {
	"modDisplayName": "True Server Reticle",
	"enabled": True,
	"column1": [
		templates.createCheckbox("Show dispersion number", 
			"showDispersionNumber", 
			True, 
			tooltip="{HEADER}Show dispersion number{/HEADER}{BODY}Shows the gun dispersion just below the crosshair as a number{/BODY}"),
		templates.createCheckbox("Enable gun rotation fix", 
			"gunRotationFix", 
			True, 
			tooltip="{HEADER}Enable gun rotation fix{/HEADER}{BODY}Fixes gun rotation being desynced from the server even if using server reticle.\nThis may cause animations to become jerky or stuttery.\nDoesn't work if the \"Enable Server Reticle\" setting is off!{/BODY}")
	]
}

settings = {
	"enabled": True,
	"showDispersionNumber": True,
	"gunRotationFix": True
}

def detour_function(old, new):
	def run(*args, **kwargs):
		return new(old, *args, **kwargs)

	return run

def DrawText(id, x, y, text, scale):
	global COMPONENT_TYPE
	global g_guiFlash
	g_guiFlash.deleteComponent(id)

	if settings["enabled"]:
		g_guiFlash.createComponent(id, COMPONENT_TYPE.LABEL, {'text': text})
		g_guiFlash.updateComponent(id, {'alignX': 'center', 'x': x, 'y': y, 'scaleX': scale, 'scaleY': scale})

# Called when the dispersion is changed
def PlayerAvatar_GetShotAngle(original, self, turretRotationSpeed, withShot = 0):
	global settings
	result = original(self, turretRotationSpeed, withShot)
	dispersion = result[0] * 100 # result[1] would be client-side dispersion
	real_dispersion = dispersion / 1.71

	if settings["showDispersionNumber"]:
		screen_height = BigWorld.screenHeight()
		DrawText("CurrentDispersion", 0, round(screen_height * 0.52), ("{:.3f}").format(real_dispersion), 1.75)

	return result

# Updates the crosshair's attributes when not using server reticle
def AvatarInputHandler_UpdateClientGunMarker(original, self, pos, direction, size, relaxTime, collData):
	global settings
	if (self._AvatarInputHandler__ctrlModeName in whitelisted_modes) and settings["enabled"]:
		size = tuple(x / 1.71 for x in size)
	return original(self, pos, direction, size, relaxTime, collData)

# Updates the crosshair's attributes when using server reticle
def AvatarInputHandler_UpdateServerGunMarker(original, self, pos, direction, size, relaxTime, collData):
	global settings
	if (self._AvatarInputHandler__ctrlModeName in whitelisted_modes) and settings["enabled"]:
		size = tuple(x / 1.71 for x in size)
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
	AvatarInputHandler.updateGunMarker = detour_function(AvatarInputHandler.updateGunMarker, AvatarInputHandler_UpdateClientGunMarker)
	AvatarInputHandler.updateGunMarker2 = detour_function(AvatarInputHandler.updateGunMarker2, AvatarInputHandler_UpdateServerGunMarker)

	# Register settings
	# def getModSettings(linkage, template=None)
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