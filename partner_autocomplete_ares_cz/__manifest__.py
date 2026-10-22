###################################################################################
#
#    Copyright (c) 2022 Data Dance s.r.o.
#
#    Data Dance Proprietary License v1.0
#
#    This software and associated files (the "Software") may only be used
#    (executed, modified, executed after modifications) if you have
#    purchased a valid license from Data Dance s.r.o.
#
#    The above permissions are granted for a single database per purchased
#    license. Furthermore, with a valid license it is permitted to use the
#    software on other databases as long as the usage is limited to a testing
#    or development environment.
#
#    You may develop modules based on the Software or that use the Software
#    as a library (typically by depending on it, importing it and using its
#    resources), but without copying any source code or material from the
#    Software. You may distribute those modules under the license of your
#    choice, provided that this license is compatible with the terms of the
#    Data Dance Proprietary License (For example: LGPL, MIT, or proprietary
#    licenses similar to this one).
#
#    It is forbidden to publish, distribute, sublicense, or sell copies of
#    the Software or modified copies of the Software.
#
#    The above copyright notice and this permission notice must be included
#    in all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
#    OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###################################################################################

{
    "name": "Partner Autocomplete using ARES CZ",
    "category": "Tools",
    "license": "AGPL-3",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "18.0.2.0.0",
    "summary": """
Completes Partner information using ARES from https://wwwinfo.mfcr.cz/
    """,
    "depends": ["partner_autocomplete_dispatcher"],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "web.assets_tests": [
            "partner_autocomplete_ares_cz/static/tests/tours/*.js",
        ],
    },
    "installable": True,
    "price": 150.00,
    "currency": "EUR",
}
