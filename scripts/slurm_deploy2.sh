#!/bin/bash

"$@"        
success=\$?

if [ \$success -ne 0 ]; then
  echo "Error code: \${success}"
fi

