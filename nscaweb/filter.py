import re

class Filter():
	'''Class for filtering incoming data'''
	def __init__(self,config,logger):
		self.config = config
		self.logger = logger
		self.pattern = re.compile("^(\[[\d]+\])[ ]*([^;]+)((?:;[^;]+)*)$")
		self.active = config["enable"] == "1"
		self.maxLineLength = config.get("max_line_length", 80)

	# splits command line into parts
	def parseLine(self, line):
		time = command = params = None
		match = self.pattern.match(line)
		if match is not None:
			time = match.group(1)
			command = match.group(2)
			if match.group(3) != "":
				params = match.group(3).split(";")[1:]
		return {
			"time": time,
			"command": command,
			"params": params
		}

	# filter checks based on host
	def filterHostChecks(self, detail, user):
		if (detail["command"].lower() != "process_service_check_result" or
		detail["params"] is None or len(detail["params"]) < 1):
			return True

		host = detail["params"][0]
		try:
			hostConfig = self.config["hosts"][host]
			users = hostConfig.as_list("users")
			if not user in users:
				self.logger.info("user %s not authorized for host %s"%(user, host))
				return True

		except Exception:
			self.logger.warn("host config for %s doesn't exist" % host)
			return True
		return False

	def apply(self, lines, user):
		if not self.active:
			return lines

		result = []
		for i in range(len(lines)):
			detail = self.parseLine(lines[i])
			filtered = False

			if detail["time"] is None or detail["command"] is None:
				filtered = True
			filtered = filtered or self.filterHostChecks(detail, user)
			print "maxlinelength", self.maxLineLength

			if filtered:
				self.logger.info("line %d filtered: %s" % (i, lines[i][:80]))
			else:
				result.append(lines[i])
		return result
