utils = {}
function utils.is_mime_sensitive(doc)
  local output_file = doc.output_file
  return string.match(output_file, "%.pdf$") or string.match(output_file, "%.tex$")
end
function utils.endpoint_fn(doc)
  local key = doc.input_file

  local file_path = debug.getinfo(1, "S").source:sub(2)
  local file_dir = file_path:match("(.*[/\\])")
  local endpoint_script = file_dir .. "endpoint.py"

  -- PDFs / LaTeX have to be handled specifically for mimetypes
  -- Need to pass in a string as arg in python invocation.
  local mime_sensitive = "no"
  if utils.is_mime_sensitive(doc) then
    mime_sensitive = "yes"
  end

  function from_endpoint(endpoint, text)
    text = text or ""
    return pandoc.pipe("python", {endpoint_script, key, endpoint, mime_sensitive}, text)
  end
  return from_endpoint
end

return utils
