function lab2_variant11
% Синтез регулятора с фиксированным конечным состоянием. Вариант 11.
T = 9;
A = [0 4; 1 0];
B = [0; 1];
Q = [1 1; 1 9];
R = 7;
x0 = [0; 0];
xTarget = [1; 0];
K = [2.5 5];

% Решение краевых условий для мод, убывающих от концов интервала.
r = sqrt((65 + [-1 1]*sqrt(641))/14);
boundary = [modeBasis(0,0,T,r); modeBasis(0,1,T,r);
            modeBasis(T,0,T,r); modeBasis(T,1,T,r)];
coefficients = boundary \ [x0(1); 4*x0(2); xTarget(1); 4*xTarget(2)];
reference = @(t,k,a) referenceProfile(t,k,a,T,r,coefficients);
opts = odeset('RelTol',1e-11,'AbsTol',1e-13);
t = linspace(0,T,901).';
[x,u,J] = simulate(t,1,0,x0,A,B,Q,R,K,reference,opts);
[xReference,uReference] = reference(t,1,0);
terminalError = norm(x(end,:).'-xTarget,inf);
assert(terminalError < 1e-8, 'Конечное состояние не достигнуто.');
assert(max(abs(x-xReference),[],'all') < 1e-8);
assert(max(abs(u-uReference)) < 1e-8);
assert(all(diff(J) >= -1e-11));

% Независимая проверка по гамильтоновой краевой системе.
hamiltonianMatrix = [A, B*B.'/(2*R); 2*Q, -A.'];
bvp = bvp4c(@(~,z) hamiltonianMatrix*z, ...
    @(left,right) [left(1:2)-x0; right(1:2)-xTarget], ...
    bvpinit(linspace(0,T,100),zeros(4,1)), ...
    bvpset('RelTol',1e-9,'AbsTol',1e-11));
zBvp = deval(bvp,t.');
assert(max(abs(zBvp(1:2,:).'-x),[],'all') < 1e-8);
assert(max(abs(zBvp(4,:).'/(2*R)-u)) < 1e-8);
assert(abs(zBvp(3,end)/2-J(end)) < 1e-8);

% Варьируется один параметр за раз: масштаб k или форма alpha.
k = [0.90; 0.95; 1; 1.05; 1.10; 1; 1; 1; 1];
alpha = [0; 0; 0; 0; 0; -0.10; -0.05; 0.05; 0.10];
C = 1024*T/315 + 416/(21*T) + 448/(5*T^3);
endState = zeros(numel(k),2);
totalCost = zeros(size(k));
for i = 1:numel(k)
    [xTest,~,JTest] = simulate([0; T],k(i),alpha(i),x0,A,B,Q,R,K,reference,opts);
    endState(i,:) = xTest(end,:);
    totalCost(i) = JTest(end);
    assert(norm(endState(i,:).'-k(i)*xTarget,inf) < 1e-8);
    assert(abs(totalCost(i) - (k(i)^2*J(end) + alpha(i)^2*C)) < 1e-8);
end
changePercent = 100*(totalCost/J(end)-1);
sensitivity = table(k,alpha,endState(:,1),endState(:,2),totalCost,changePercent, ...
    'VariableNames',{'k','alpha','x1Final','x2Final','J','changePercent'});
trajectory = table(t,x(:,1),x(:,2),u,J,'VariableNames',{'t','x1','x2','u','J'});

outDir = fullfile(fileparts(mfilename('fullpath')),'results');
if ~isfolder(outDir)
    mkdir(outDir);
end
writetable(trajectory,fullfile(outDir,'trajectory.csv'));
writetable(sensitivity,fullfile(outDir,'sensitivity.csv'));
plotSignals(t,x,u,J,fullfile(outDir,'optimal_signals.png'));

fprintf('r: %.12g %.12g\n',r);
fprintf('Mode coefficients: %.12g %.12g %.12g %.12g\n',coefficients);
fprintf('J*: %.12f | C: %.12f | terminal error: %.3e\n',J(end),C,terminalError);
fprintf('Independent J via costate: %.12f\n',zBvp(3,end)/2);
disp(sensitivity);
end

function basis = modeBasis(t,order,T,r)
t = t(:);
basis = [exp(-t*r).*(-r).^order, exp(-(T-t)*r).*r.^order];
end

function [x,u] = referenceProfile(t,k,alpha,T,r,coefficients)
s = t(:)/T;
h = 16*s.^2.*(1-s).^2;
dh = 32*s.*(1-s).*(1-2*s)/T;
ddh = 32*(1-6*s+6*s.^2)/T^2;
q = k*(modeBasis(t,0,T,r)*coefficients) + alpha*h;
dq = k*(modeBasis(t,1,T,r)*coefficients) + alpha*dh;
ddq = k*(modeBasis(t,2,T,r)*coefficients) + alpha*ddh;
x = [q,dq/4];
u = ddq/4-q;
end

function [x,u,J] = simulate(t,k,alpha,x0,A,B,Q,R,K,reference,opts)
solution = ode45(@(time,z) closedLoop(time,z,k,alpha,A,B,Q,R,K,reference), ...
    [t(1) t(end)],[x0; 0],opts);
z = deval(solution,t.').';
x = z(:,1:2);
J = z(:,3);
[xRef,uRef] = reference(t,k,alpha);
u = uRef-(x-xRef)*K.';
end

function dz = closedLoop(t,z,k,alpha,A,B,Q,R,K,reference)
x = z(1:2);
[xRef,uRef] = reference(t,k,alpha);
u = uRef-K*(x-xRef.');
dz = [A*x+B*u; x.'*Q*x+R*u^2];
end

function plotSignals(t,x,u,J,outputFile)
f = figure('Visible','off','Color','w','Position',[100 100 1050 730]);
tiledlayout(f,2,2,'TileSpacing','compact','Padding','compact');
labels = {'x_1^*(t)','x_2^*(t)','u^*(t)','J(t)'};
signals = [x,u,J];
for i = 1:numel(labels)
    ax = nexttile;
    plot(ax,t,signals(:,i),'LineWidth',2,'Color',[0.10 0.26 0.48]);
    grid(ax,'on');
    box(ax,'on');
    xlim(ax,[t(1),t(end)]);
    xticks(ax,0:1:t(end));
    xlabel(ax,'t, с','Color','k');
    ylabel(ax,labels{i},'Color','k');
    ax.FontSize = 14;
    ax.Color = 'white';
    ax.XColor = 'k';
    ax.YColor = 'k';
    ax.GridColor = [0.65 0.65 0.65];
    ax.GridAlpha = 0.30;
end
exportgraphics(f,outputFile,'Resolution',220,'BackgroundColor','white');
close(f);
end
