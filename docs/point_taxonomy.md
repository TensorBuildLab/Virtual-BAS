# Point taxonomy: what a BAS measures today, and what it should measure

EmuBAS exposes **1,207 points on 54 pieces of equipment** for the DOE large office:

| Tier | Points | Meaning |
|---|---|---|
| **standard** | 508 | Found in a typical commercial BAS today: ASHRAE Guideline 36 (G36) hard-wired and software points, vendor chiller integrations, utility meters |
| **advanced** | 244 | Found in well-instrumented or recently commissioned BAS |
| **next_gen** | 295 | Rarely installed today but valuable for analytics, IEQ and AI |
| **truth** | 160 | Ground truth only, not measurable by a BAS (true occupants, coil loads, OA fraction, …) |

The full list is in [point_list_large_office.md](point_list_large_office.md). Every point carries:
- **`tier`** — the availability tier above.
- **`source`** — where its true value comes from:
  - `energyplus`: inner-space physics;
  - `model`: an outer-space physical model driven by EnergyPlus flows;
  - `surrogate`: an engineering correlation;
  - `bas`: calculated by the BAS from present values.
- **`sensor_class`** — its data-sheet error model.

Because EmuBAS knows the truth of every point, it can quantify the **value of information** of a sensor package. For example, you can compare FDD accuracy with and without valve feedback or coil BTU meters. To do that, restrict the exposed points with `point_tiers` in the scenario or `building.yaml`:

```yaml
point_tiers: [standard]            # emulate a typical BAS of today (truth is still recorded)
```

The tier filter decides which points are exposed through the API/GUI and recorded in the observed tables. The built-in control sequences always receive the inputs they are programmed with.

## 1. Why a "next-generation" tier

Field evidence shows that today's BAS have many temperatures and set points but few meters, little actuator feedback, little indoor environmental quality (IEQ) data beyond T/RH/CO2, and no grid signals.

* **Point coverage (90 buildings).** Brick-modelled BAS data from 90 buildings contained 7,380 temperature streams but only 77 power meters. Only 8 % of the buildings had the points needed for an EUI calculation, 16 % for HVAC energy disaggregation and 3 % for rogue-zone airflow detection (Fierro et al., *Mortar*, ACM TOSN 2019, https://escholarship.org/uc/item/7700b448).
* **CO2 sensor accuracy in the field.** 208 CO2 sensors in 34 buildings had mean absolute errors of 118–138 ppm. 40–47 % of them were outside ±75 ppm (Fisk et al., LBNL 2010, https://eta-publications.lbl.gov/publications/co2-monitoring-demand-controlled).
* **VAV airflow accuracy.** Measurement errors are ±8–40 % at low flow (Drexel dissertation, https://researchdiscovery.drexel.edu/esploro/outputs/doctoral/991014632200004721).
* **FDD sensor requirements.** FDD tools often need add-on sensors that the BAS does not have (Granderson et al., LBNL 2017, https://eta-publications.lbl.gov/publications/characterization-and-survey-automated).
* **DOE research priorities.** DOE BTO lists multi-function wireless sensors, sub-metering, occupant-centric sensing and virtual sensing as priorities (https://www.energy.gov/sites/prod/files/2019/04/f61/bto-sc-rdo-041519.pdf).
* **Semantic-model gaps.** Brick 1.4 has classes for PM, TVOC, occupancy counts, vibration and thermal power. It still has none for sound level, mean radiant temperature, PMV/PPD, electricity price, grid carbon intensity, demand-response events or occupant complaints. In EmuBAS these points have Haystack-style tags and an empty `brick` field.

## 2. What is modelled, by equipment

### Zones (per thermal zone)
| Group | Points | Tier | Source / model |
|---|---|---|---|
| Thermal | ZN-T, HTG/CLG-SP, OCC-MODE, ZN-T-ADJ (writable occupant adjust ±3 K) | standard | EnergyPlus |
| | ZN-RH, ZN-DP | advanced | EnergyPlus |
| | ZN-MRT (globe), ZN-OPT, PMV, PPD (comfort station) | next_gen | EnergyPlus (Fanger model of the People object) |
| Air quality | ZN-CO2 | standard (DCV zones) | EnergyPlus contaminant balance |
| | ZN-PM25, ZN-PM10, ZN-TVOC | next_gen | outer-space mass balance driven by EnergyPlus supply air, OA fraction, infiltration and occupants (§3) |
| Light | ZN-LUX, LIGHT-LVL | advanced | lumen method (electric) + daylight-flux method from EnergyPlus transmitted window solar |
| Sound | ZN-DBA | next_gen | fan-law terminal noise + speech + background (§3) |
| Occupancy | ZN-OCC (PIR) | standard | EnergyPlus occupants (Markov occupancy model) |
| | OCC-COUNT (people counter) | next_gen | same truth, people-counter error model |
| | WIN-STS (window contact, G36 `u1Win`) | advanced | `window_open` events |
| Feedback | TS-VOTE (app), HOT-CALLS, COLD-CALLS (work orders) | next_gen | stochastic occupant model driven by EnergyPlus PMV/PPD |
| Energy | LIGHT-KW (panel), PLUG-KW (circuit) | advanced / next_gen | EnergyPlus |
| Truth | OCCUPANTS, DAYLIGHT-LUX, INFIL-ACH, WIN-SOL-KW, WIN-Q-KW, INT-GAIN-KW, SYS-CLG/HTG-KW | truth | EnergyPlus |

### VAV terminals
| Points | Tier |
|---|---|
| DA-F, DA-T, DA-F-SP, DMPR-CMD, CLG/HTG-LOOP, ZN-MODE, CLG-REQ / PRS-REQ / HW-REQ (G36 requests 0–3), LOW-FLOW-ALM (G36: < 70 % of set point for 5 min) | standard |
| DMPR-POS, RHV-POS (position *feedback*), DA-VP (flow-cross velocity pressure) | advanced |
| RH-BTU, RH-WF (reheat-coil BTU meter and water flow) | next_gen |

### Air handling units
| Points | Tier |
|---|---|
| SA-T, MA-T, RA-T, SA-F, OA-F (AFMS), local OA-T, SF-CMD/STS/SPD/HZ/KW, DSP, FLT-DP, FRZ-STAT, SMK-DET, set points, ECON-EN, OA-FRAC-CALC (from temperatures), SF-RUNHRS/STARTS | standard |
| SA-RH, RA-RH, OA-RH, SA-DP, RA-CO2, HC-LAT, CC-LAT, OAD/CCV/HCV-POS feedback, SF-AMPS, OA-FRAC-AFMS, SF-W-PER-CMS | advanced |
| CC-EWT/LWT/WF/BTU, HC-BTU, CC-DP (coil air-side ΔP), SF-VIB (ISO 10816 velocity) | next_gen |

### Central plant
| Equipment | Standard | Advanced | Next-gen |
|---|---|---|---|
| Chiller | KW, STS, CHW/CDW entering/leaving temperatures, PCT-RLA, ALM, KW-TON, run-hours, starts | LOAD (BTU), CHW-F, CDW-F, EVAP/COND-SAT-T, EVAP/COND-P (vendor BACnet panel) | – |
| Boiler | STS, HW-LWT/EWT, FIRE-RATE, ALM, run-hours | LOAD, GAS-KW, HW-F, FLUE-T | – |
| Cooling tower | FAN-KW, FAN-STS, FAN-SPD, LWT, EWT, APPROACH, RANGE | MAKEUP-F (water meter) | – |
| Pumps | KW, SPD, HZ, STS, run-hours, starts | – | VIB |
| Loops | ST, RT, F, DP, ST-SP, ΔT, CHW-TONS | PLANT-KW-TON | – |
| DHW heater | – | TANK-T, STS, GAS-KW | USE-F |
| Plenums | – | T | – |

### Weather station, meters, grid
| Group | Standard | Advanced | Next-gen |
|---|---|---|---|
| Weather | OA-T, OA-RH, HDD/CDD | OA-WB, OA-DP, OA-H, OA-W, BARO, WIND, WIND-DIR, SOLAR (GHI), OA-LUX, RAIN | DNI, DHI, SKY-COVER, SKY-T, PRECIP, OA-PM25/PM10, 1/6/24 h forecasts of OA-T and GHI |
| Meters | building electricity and gas demand, water flow, kWh/gas/water totalisers, 15-min demand, daily/monthly peak | end-use sub-meters (HVAC, lighting, cooling, fans, pumps, heat rejection, heating gas, exterior lights, DHW gas), tower make-up water | plug-load and elevator sub-meters |
| Grid | – | – | TOU price and period, marginal carbon intensity, DR event and requested shed, cost and carbon today |

## 3. Outer-space environment models (`virtualbas/realworld/environment.py`)

EnergyPlus provides the flows; these models add the quantities EnergyPlus does not solve.

* **Particles and VOC.** A well-mixed balance for each zone:
  - Balance: $V\,dC/dt = Q_s C_s + P Q_i C_o + S - (Q_s + Q_i + kV) C$.
  - Supply concentration: $C_s = (1-\eta)(x_{OA}C_o + (1-x_{OA})\bar C_{ret})$.
  - Integration: exact over each step.
  - Fractions modelled: PM2.5 and the coarse fraction PM2.5–10 (PM10 = PM2.5 + coarse); TVOC has no filtration.
  - Defaults: MERV 8 filter (η = 0.25 fine, 0.75 coarse); penetration 0.8 / 0.6; deposition 0.2 / 1.0 h⁻¹.
  - Sources: per person 0.1 / 0.5 mg h⁻¹ for PM2.5 / coarse; TVOC 3 mg h⁻¹ per person plus 0.1 mg m⁻² h⁻¹ from materials.
  - Outdoor PM2.5: a log-normal Ornstein–Uhlenbeck process (mean 8 µg m⁻³, 18 h correlation) with a traffic cycle.
  - Events: `wildfire_smoke`, `indoor_pollutant_source`; fault: `filter_bypass`.
* **Illuminance.**
  - Model: $E = E_d P_{light}/P_{light,d} + K_v U \Phi_{sol}/A$.
  - Parameters: $E_d$ = 500 lx at design lighting power, $K_v$ = 105 lm W⁻¹, $U$ = 0.4.
  - $\Phi_{sol}$ is EnergyPlus' transmitted window solar.
* **Sound.**
  - Model: $L = 10\log_{10}\sum 10^{L_j/10}$.
  - Terms: terminal noise 40 dBA at design flow + 50 log₁₀(V/Vmax) (fan law); speech 45 dBA at 1 talker per 100 m² (15 % of occupants talking); background 30 dBA.
* **Occupant feedback.**
  - Votes: round(PMV + N(0, 1)) clipped to ±3, at 0.05 votes per occupant-hour.
  - Complaints: Poisson with rate $N\,r_c\,\mathrm{PPD}/100$ ($r_c$ = 0.08 h⁻¹), split hot/cold by a logistic function of PMV.
* **Weather forecast.**
  - Basis: weather file plus lead-time-dependent errors, AR(1) between hourly issues.
  - Temperature error: σ(h) = 0.4 + 2.2(1 − e^{−h/30}) K.
  - GHI error: 8–43 % relative.
  - Also available as `GET /api/forecast` and the MCP tool `weather_forecast`.
* **Grid.**
  - Tariff: TOU (0.08 / 0.14 / 0.24 $/kWh).
  - Carbon intensity: synthetic marginal value (0.40 kg kWh⁻¹ base, evening peak, solar "duck" dip, AR noise).
  - Events: `demand_response` (OpenADR-style shed request) and `price_spike`.
* **Surrogates.**
  - Chiller refrigerant: saturated temperatures from approach temperatures that grow with load and fouling; R-134a pressures from ln p[kPa] = 15.422 − 2661/T[K].
  - Boiler flue temperature: rises with firing rate and fouling.
  - Fan and pump vibration: ∝ speed², plus bearing wear for fans (`fan_degradation`).
  - Coil air-side ΔP: ∝ flow^1.8.

## 4. Sensor accuracy (data sheets → `virtualbas/realworld/sensors.py`)

| Class | Model (bias σ / gain σ / noise σ / τ) | Basis |
|---|---|---|
| Temperature (zone / duct / water) | 0.2 / – / 0.05 K, 30–120 s | thermistor ±0.2 °C element; installed ±0.3–0.5 K |
| RH (indoor / outdoor) | 1.5 / 2.5 %RH, drift ≈ 1 %RH/yr | Vaisala HMW90 ±1.7–3 %RH, 0.5 %RH/yr |
| CO2 (NDIR) | 20 ppm + 1 % gain, drift | GMW90 ±(30 ppm + 2 %); field MAE ≈ 120 ppm (use `sensor_bias` / `realism` for degraded fleets) |
| PM (optical) | 1.5 µg m⁻³ / 15 % / 1 µg m⁻³ | SPS30 ±(5 µg m⁻³ + 5 %); field R² 0.64–0.85 (AQ-SPEC) |
| TVOC (MOx) | 20 µg m⁻³ / 35 % / OU baseline drift | relative accuracy only (RESET ±15–20 %) |
| Illuminance | – / 10 % / 5 lx | photosensor ±5–10 % |
| Sound | 0.7 / – / 1.0 dB | IEC 61672 class 2 ±1.4 dB |
| Globe (MRT) | 0.3 K, τ = 20 min | ISO 7726 |
| People counter | – / 5 % / 0.6 persons | camera/thermopile 90–98 % accuracy vs PIR 73 % |
| BTU meter | – / 3 % / 0.5 kW | EN 1434 class 2–3 |
| Refrigerant pressure | 5 kPa / 0.5 % / 2 kPa | chiller panel transducers |
| Vibration | – / 5 % / 0.1 mm s⁻¹ | ISO 10816 velocity transducer |

## 5. Not yet modelled (contributions welcome)

These are not modelled yet:
- **Air-side controls:** building static pressure, and return/relief fans (not in the reference model).
- **Pollutants:** ozone, NO2, CO, formaldehyde, radon.
- **Envelope sensing:** glare (DGP), envelope heat-flux plates and surface temperatures, blinds.
- **Distributed energy:** PV, batteries and EV chargers.
- **Water treatment:** conductivity and blowdown.
- **Device diagnostics:** chiller oil pressure and discharge temperature, network/device health.
