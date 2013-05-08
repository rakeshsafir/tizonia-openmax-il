/**
 * Copyright (C) 2011-2013 Aratelia Limited - Juan A. Rubio
 *
 * This file is part of Tizonia
 *
 * Tizonia is free software: you can redistribute it and/or modify it under the
 * terms of the GNU Lesser General Public License as published by the Free
 * Software Foundation, either version 3 of the License, or (at your option)
 * any later version.
 *
 * Tizonia is distributed in the hope that it will be useful, but WITHOUT ANY
 * WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for
 * more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with Tizonia.  If not, see <http://www.gnu.org/licenses/>.
 */

/**
 * @file   fwprc_decls.h
 * @author Juan A. Rubio <juan.rubio@aratelia.com>
 *
 * @brief  Tizonia OpenMAX IL - Binary Writer processor class decls
 *
 *
 */

#ifndef FWPRC_DECLS_H
#define FWPRC_DECLS_H

#ifdef __cplusplus
extern "C"
{
#endif

#include "fwprc.h"
#include "tizproc_decls.h"

#include <stdbool.h>

  typedef struct fw_prc fw_prc_t;
  struct fw_prc
  {
    /* Object */
    const tiz_prc_t _;
    FILE *p_file_;
    OMX_PARAM_CONTENTURITYPE *p_uri_param_;
    OMX_U32 counter_;
    bool eos_;
  };

#ifdef __cplusplus
}
#endif

#endif                          /* FWPRC_DECLS_H */